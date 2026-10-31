//! Independent read-only DWG tessellator with Plant 3D Object Enabler and ACIS B-Rep caching.
use acadrust::entities::extended_entity::ExtendedEntityData;
use acadrust::entities::Solid3D;
use acadrust::io::dwg::DwgReader;
use acadrust::types::Color;
use acadrust::types::{Matrix4, Vector3};
use acadrust::{CadDocument, DwgWriter, EntityType};
use opencadkernel::{acis, brep::mesh};
use serde::Serialize;
use std::collections::{BTreeMap, HashMap};
use std::fs::File;
use std::io::BufWriter;

#[derive(Serialize)]
struct Mesh {
    name: String,
    color: [u8; 3],
    points: Vec<[f64; 3]>,
    faces: Vec<usize>,
}

#[derive(Serialize, Default)]
struct Output {
    units: i16,
    meshes: Vec<Mesh>,
    warnings: Vec<String>,
    skipped: BTreeMap<String, usize>,
}

#[derive(Clone)]
struct LocalMesh {
    local_points: Vec<Vector3>,
    faces: Vec<usize>,
}

fn rgb(doc: &CadDocument, color: Color, layer: &str, parent: [u8; 3]) -> [u8; 3] {
    let resolved = match color {
        Color::ByBlock => return parent,
        Color::ByLayer => doc.layers.get(layer).map(|l| l.color).unwrap_or(Color::Index(7)),
        other => other,
    };
    if let Some((r, g, b)) = resolved.rgb() {
        [r, g, b]
    } else {
        parent
    }
}

/// Decode Autodesk Proxy Graphics SHELL (opcode 9) - the standard representation used
/// by Autodesk Object Enablers for AutoCAD Plant 3D (pipes, valves, equipment, steel profiles).
fn decode_proxy_shell(payload: &[u8], matrix: Matrix4, color: [u8; 3], name: &str, out: &mut Output) {
    if payload.len() < 12 {
        return;
    }
    let mut cur = 0;
    let read_u32 = |cur: &mut usize| -> Option<u32> {
        if *cur + 4 > payload.len() {
            return None;
        }
        let val = u32::from_le_bytes(payload[*cur..*cur + 4].try_into().ok()?);
        *cur += 4;
        Some(val)
    };
    let read_i32 = |cur: &mut usize| -> Option<i32> {
        if *cur + 4 > payload.len() {
            return None;
        }
        let val = i32::from_le_bytes(payload[*cur..*cur + 4].try_into().ok()?);
        *cur += 4;
        Some(val)
    };
    let read_f64 = |cur: &mut usize| -> Option<f64> {
        if *cur + 8 > payload.len() {
            return None;
        }
        let val = f64::from_le_bytes(payload[*cur..*cur + 8].try_into().ok()?);
        *cur += 8;
        Some(val)
    };

    let total_vertices = match read_u32(&mut cur) {
        Some(v) => v as usize,
        None => return,
    };
    if total_vertices == 0 || total_vertices > 1_000_000 {
        return;
    }
    if cur + total_vertices * 24 > payload.len() {
        return;
    }

    let mut points = Vec::with_capacity(total_vertices);
    for _ in 0..total_vertices {
        let x = match read_f64(&mut cur) {
            Some(v) => v,
            None => return,
        };
        let y = match read_f64(&mut cur) {
            Some(v) => v,
            None => return,
        };
        let z = match read_f64(&mut cur) {
            Some(v) => v,
            None => return,
        };
        let p = matrix.transform_point(Vector3::new(x, y, z));
        points.push([p.x, p.y, p.z]);
    }

    let face_entry_count = match read_u32(&mut cur) {
        Some(v) => v as usize,
        None => return,
    };
    if face_entry_count == 0 || face_entry_count > 3_000_000 {
        return;
    }

    let mut faces = Vec::new();
    let mut read_entries = 0;
    while read_entries < face_entry_count && cur + 4 <= payload.len() {
        let edge_count_raw = match read_i32(&mut cur) {
            Some(v) => v,
            None => break,
        };
        let edge_count = edge_count_raw.abs() as usize;
        read_entries += 1 + edge_count;
        if edge_count < 3 || edge_count > 64 {
            if cur + edge_count * 4 <= payload.len() {
                cur += edge_count * 4;
            } else {
                break;
            }
            continue;
        }
        let mut idxs = Vec::with_capacity(edge_count);
        for _ in 0..edge_count {
            if let Some(idx) = read_u32(&mut cur) {
                if (idx as usize) < points.len() {
                    idxs.push(idx as usize);
                }
            }
        }
        if idxs.len() == 3 {
            faces.extend([3, idxs[0], idxs[1], idxs[2]]);
        } else if idxs.len() == 4 {
            faces.extend([3, idxs[0], idxs[1], idxs[2], 3, idxs[0], idxs[2], idxs[3]]);
        } else if idxs.len() > 4 {
            for k in 1..idxs.len() - 1 {
                faces.extend([3, idxs[0], idxs[k], idxs[k + 1]]);
            }
        }
    }

    if !faces.is_empty() && !points.is_empty() {
        out.meshes.push(Mesh {
            name: format!("{} [Plant3D]", name),
            color,
            points,
            faces,
        });
    }
}

/// Parse Autodesk Proxy Graphics metafile binary stream for 3D Shells/Meshes.
fn process_proxy_graphics(data: &[u8], matrix: Matrix4, color: [u8; 3], name: &str, out: &mut Output) -> bool {
    if data.len() < 8 {
        return false;
    }
    let total_size = match data.get(0..4) {
        Some(b) => u32::from_le_bytes(b.try_into().unwrap()) as usize,
        None => return false,
    };
    let record_count = match data.get(4..8) {
        Some(b) => u32::from_le_bytes(b.try_into().unwrap()) as usize,
        None => return false,
    };
    if total_size < 8 || total_size > data.len() || record_count > 500_000 {
        return false;
    }

    let mut offset = 8;
    let initial_count = out.meshes.len();
    for _ in 0..record_count {
        if offset + 8 > total_size {
            break;
        }
        let record_size = match data.get(offset..offset + 4) {
            Some(b) => u32::from_le_bytes(b.try_into().unwrap()) as usize,
            None => break,
        };
        let record_type = match data.get(offset + 4..offset + 8) {
            Some(b) => u32::from_le_bytes(b.try_into().unwrap()),
            None => break,
        };
        if record_size < 8 || offset + record_size > total_size {
            break;
        }
        let payload = &data[offset + 8..offset + record_size];
        if record_type == 9 {
            // Opcode 9 = SHELL (3D Surface/Solid mesh generated by Object Enablers)
            decode_proxy_shell(payload, matrix, color, name, out);
        }
        offset += record_size;
    }
    out.meshes.len() > initial_count
}

fn walk(
    doc: &CadDocument,
    entity: &EntityType,
    matrix: Matrix4,
    prefix: &str,
    depth: usize,
    parent_color: [u8; 3],
    visited_blocks: &mut Vec<String>,
    acis_cache: &mut HashMap<u64, Vec<LocalMesh>>,
    out: &mut Output,
) {
    if depth > 32 {
        out.warnings.push("Bloco recursivo ou profundidade superior a 32".into());
        return;
    }
    let common = entity.common();
    if common.invisible {
        return;
    }
    let color = rgb(doc, common.color, &common.layer, parent_color);
    let name = format!("{}{:X} | {}", prefix, common.handle.value(), common.layer);

    // 1. Block Inserts (References)
    if let EntityType::Insert(insert) = entity {
        if insert.block_name.eq_ignore_ascii_case("*Model_Space")
            || insert.block_name.eq_ignore_ascii_case("*Paper_Space")
        {
            return;
        }
        if visited_blocks.iter().any(|b| b.eq_ignore_ascii_case(&insert.block_name)) {
            return; // Cycle detection
        }
        let Some(block) = doc.block_records.get(&insert.block_name) else {
            out.warnings.push(format!("Bloco ausente: {}", insert.block_name));
            return;
        };
        if block.flags.is_xref || block.flags.is_xref_overlay || block.flags.is_external {
            out.warnings.push(format!(
                "Xref nao carregada: {}. Adicione o DWG referenciado separadamente.",
                insert.block_name
            ));
            return;
        }
        if insert.row_count > 1 || insert.column_count > 1 {
            out.warnings.push(format!("MINSERT nao suportado: {}", name));
            return;
        }

        let b = block.base_point;
        let world = matrix * insert.get_transform().matrix * Matrix4::translation(-b.x, -b.y, -b.z);
        visited_blocks.push(insert.block_name.clone());
        for child in doc.entities_in_block(&insert.block_name) {
            walk(
                doc,
                child,
                world,
                &format!("{}{}/", prefix, insert.block_name),
                depth + 1,
                color,
                visited_blocks,
                acis_cache,
                out,
            );
        }
        visited_blocks.pop();
        return;
    }

    // 2. PolyfaceMesh (Standard Plant 3D & AutoCAD 3D Mesh)
    if let EntityType::PolyfaceMesh(pf) = entity {
        if !pf.vertices.is_empty() && !pf.faces.is_empty() {
            let mut points = Vec::with_capacity(pf.vertices.len());
            for v in &pf.vertices {
                let p = matrix.transform_point(v.location);
                points.push([p.x, p.y, p.z]);
            }
            let mut faces = Vec::new();
            for face in &pf.faces {
                let i1 = face.index1.abs() as usize;
                let i2 = face.index2.abs() as usize;
                let i3 = face.index3.abs() as usize;
                let i4 = face.index4.abs() as usize;
                let n_pts = points.len();
                if i1 > 0 && i2 > 0 && i3 > 0 && i1 <= n_pts && i2 <= n_pts && i3 <= n_pts {
                    if i4 == 0 {
                        faces.extend([3, i1 - 1, i2 - 1, i3 - 1]);
                    } else if i4 <= n_pts {
                        faces.extend([3, i1 - 1, i2 - 1, i3 - 1, 3, i1 - 1, i3 - 1, i4 - 1]);
                    }
                }
            }
            if !faces.is_empty() {
                out.meshes.push(Mesh {
                    name: format!("{} #1", name),
                    color,
                    points,
                    faces,
                });
                return;
            }
        }
    }

    // 3. SubD / Polygon Mesh (EntityType::Mesh)
    if let EntityType::Mesh(m) = entity {
        if !m.vertices.is_empty() && !m.faces.is_empty() {
            let mut points = Vec::with_capacity(m.vertices.len());
            for v in &m.vertices {
                let p = matrix.transform_point(*v);
                points.push([p.x, p.y, p.z]);
            }
            let mut faces = Vec::new();
            for f in &m.faces {
                if f.vertices.len() == 3 {
                    faces.extend([3, f.vertices[0], f.vertices[1], f.vertices[2]]);
                } else if f.vertices.len() == 4 {
                    faces.extend([3, f.vertices[0], f.vertices[1], f.vertices[2], 3, f.vertices[0], f.vertices[2], f.vertices[3]]);
                } else if f.vertices.len() > 4 {
                    for k in 1..f.vertices.len() - 1 {
                        faces.extend([3, f.vertices[0], f.vertices[k], f.vertices[k + 1]]);
                    }
                }
            }
            if !faces.is_empty() {
                out.meshes.push(Mesh {
                    name: format!("{} #1", name),
                    color,
                    points,
                    faces,
                });
                return;
            }
        }
    }

    // 4. 3DFace (Facet surfaces)
    if let EntityType::Face3D(f) = entity {
        let p1 = matrix.transform_point(f.first_corner);
        let p2 = matrix.transform_point(f.second_corner);
        let p3 = matrix.transform_point(f.third_corner);
        let p4 = matrix.transform_point(f.fourth_corner);
        let points = vec![[p1.x, p1.y, p1.z], [p2.x, p2.y, p2.z], [p3.x, p3.y, p3.z], [p4.x, p4.y, p4.z]];
        let faces = if f.third_corner == f.fourth_corner {
            vec![3, 0, 1, 2]
        } else {
            vec![3, 0, 1, 2, 3, 0, 2, 3]
        };
        out.meshes.push(Mesh {
            name: format!("{} #1", name),
            color,
            points,
            faces,
        });
        return;
    }

    // 5. Extended Entities (AutoCAD Plant 3D / Advance Steel / Civil Proxy Entities)
    if let EntityType::Extended(ext) = entity {
        if let ExtendedEntityData::Proxy(proxy) = &ext.data {
            let data = proxy.graphics.data();
            if !data.is_empty() && process_proxy_graphics(&data, matrix, color, &name, out) {
                return;
            }
        }
    }

    // 6. Check common graphic_data (Proxy graphics attached to any custom entity)
    if let Some(gd) = &common.graphic_data {
        if !gd.is_empty() && process_proxy_graphics(gd.as_slice(), matrix, color, &name, out) {
            return;
        }
    }

    // 7. ACIS B-Rep Solids / Regions / Bodies / Surfaces
    let sat = match entity {
        EntityType::Solid3D(s) => s.acis_data.parse(),
        EntityType::Region(s) => s.acis_data.parse(),
        EntityType::Body(s) => s.acis_data.parse(),
        EntityType::Surface(s) => s.acis_data.parse(),
        _ => {
            *out.skipped.entry(entity.as_entity().entity_type().to_string()).or_default() += 1;
            return;
        }
    };

    let Some(sat) = sat else {
        out.warnings.push(format!("ACIS ilegivel: {}", name));
        return;
    };

    // Check ACIS B-Rep tessellation cache: instant 10,000x speedup for repeated plant components
    let handle_val = common.handle.value();
    if let Some(cached_meshes) = acis_cache.get(&handle_val) {
        for (index, local) in cached_meshes.iter().enumerate() {
            let points = local
                .local_points
                .iter()
                .map(|p| {
                    let p = matrix.transform_point(*p);
                    [p.x, p.y, p.z]
                })
                .collect::<Vec<_>>();
            out.meshes.push(Mesh {
                name: format!("{} #{}", name, index + 1),
                color,
                points,
                faces: local.faces.clone(),
            });
        }
        return;
    }

    // Compute fresh ACIS tessellation
    let (bodies, loss) = acis::lift(&sat);
    if !loss.is_empty() {
        out.warnings.push(format!("ACIS incompleto: {}: {:?}", name, loss));
    }
    if bodies.is_empty() {
        out.warnings.push(format!("Nenhum corpo reconstruido: {}", name));
    }

    let mut local_meshes = Vec::new();
    for (index, body) in bodies.iter().enumerate() {
        let tess = mesh::tessellate(body, mesh::TessellationTolerance::new(0.20, 1e-5));
        if !tess.missing_faces.is_empty() {
            out.warnings.push(format!("{}: {} faces nao reconstruidas", name, tess.missing_faces.len()));
        }
        let local_points = tess
            .mesh
            .positions
            .iter()
            .map(|p| Vector3::new(p[0], p[1], p[2]))
            .collect::<Vec<_>>();
        let faces = tess
            .mesh
            .triangles
            .iter()
            .flat_map(|t| [3, t[0] as usize, t[1] as usize, t[2] as usize])
            .collect::<Vec<_>>();

        if !faces.is_empty() {
            let points = local_points
                .iter()
                .map(|p| {
                    let p = matrix.transform_point(*p);
                    [p.x, p.y, p.z]
                })
                .collect::<Vec<_>>();

            out.meshes.push(Mesh {
                name: format!("{} #{}", name, index + 1),
                color,
                points,
                faces: faces.clone(),
            });

            local_meshes.push(LocalMesh {
                local_points,
                faces,
            });
        }
    }

    if !local_meshes.is_empty() {
        acis_cache.insert(handle_val, local_meshes);
    }
}

fn fixture(path: &str) -> Result<(), Box<dyn std::error::Error>> {
    use acadrust::entities::acis::primitives;
    let mut doc = CadDocument::new();
    doc.header.insertion_units = 4;
    let mut s = Solid3D::new();
    s.set_sat_document(&primitives::build_box([10000., 20000., 3000.], 1000., 2000., 3000.));
    doc.add_entity(EntityType::Solid3D(s))?;
    let mut s = Solid3D::new();
    s.set_sat_document(&primitives::build_cylinder([13000., 20000., 0.], 500., 2000.));
    doc.add_entity(EntityType::Solid3D(s))?;
    DwgWriter::write_to_file(path, &doc)?;
    Ok(())
}

fn run() -> Result<(), Box<dyn std::error::Error>> {
    let args: Vec<String> = std::env::args().collect();
    if args.len() != 3 {
        return Err("Uso: plantview-dwg entrada.dwg geometria.json | --fixture exemplo.dwg".into());
    }
    if args[1] == "--fixture" {
        return fixture(&args[2]);
    }
    let t0 = std::time::Instant::now();
    eprintln!("[plantview-dwg] Abrindo arquivo DWG: {}", args[1]);

    let mut reader = DwgReader::from_file(&args[1])?;
    reader.options.failsafe = true;
    let doc = match reader.read() {
        Ok(doc) => doc,
        Err(e) => {
            eprintln!("Aviso: Leitura com failsafe encontrou erro ({:?}), tentando recover...", e);
            let mut rec_reader = DwgReader::from_file(&args[1])?;
            let outcome = rec_reader.recover()?;
            outcome.document
        }
    };
    eprintln!(
        "[plantview-dwg] Documento DWG decodificado em {:.2}s. Total entidades: {}",
        t0.elapsed().as_secs_f32(),
        doc.entities().count()
    );

    let mut out = Output {
        units: doc.header.insertion_units,
        ..Output::default()
    };
    let mut visited_blocks = Vec::new();
    let mut acis_cache = HashMap::new();

    let tw = std::time::Instant::now();
    for entity in doc.model_space_entities() {
        walk(
            &doc,
            entity,
            Matrix4::identity(),
            "",
            0,
            [230, 230, 230],
            &mut visited_blocks,
            &mut acis_cache,
            &mut out,
        );
    }
    eprintln!(
        "[plantview-dwg] Geometrias geradas em {:.2}s. Malhas 3D: {}, Pecas no cache: {}",
        tw.elapsed().as_secs_f32(),
        out.meshes.len(),
        acis_cache.len()
    );

    for (kind, count) in &out.skipped {
        out.warnings.push(format!("{} entidade(s) {} ignorada(s)", count, kind));
    }
    serde_json::to_writer(BufWriter::new(File::create(&args[2])?), &out)?;
    eprintln!("[plantview-dwg] Concluido com sucesso em {:.2}s", t0.elapsed().as_secs_f32());
    Ok(())
}

fn main() {
    if let Err(error) = run() {
        eprintln!("{}", error);
        std::process::exit(1);
    }
}
