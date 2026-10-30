//! Independent read-only DWG tessellator. Geometry stays f64 in world coordinates.
use acadrust::{CadDocument, EntityType, DwgWriter};
use acadrust::io::dwg::DwgReader;
use acadrust::entities::{Entity, Solid3D};
use acadrust::types::{Matrix4, Vector3};
use opencadkernel::{acis, brep::mesh};
use serde::Serialize;
use std::{collections::BTreeMap, fs::File, io::BufWriter};

#[derive(Serialize)]
struct Mesh { name: String, points: Vec<[f64;3]>, faces: Vec<usize> }
#[derive(Serialize, Default)]
struct Output { units: i16, meshes: Vec<Mesh>, warnings: Vec<String>, skipped: BTreeMap<String,usize> }

fn walk(doc: &CadDocument, entity: &EntityType, matrix: Matrix4, prefix: &str, depth: usize, out: &mut Output) {
    if depth > 32 { out.warnings.push("Bloco recursivo ou profundidade superior a 32".into()); return; }
    let common = entity.common();
    if common.invisible { return; }
    let name = format!("{}{:X} | {}", prefix, common.handle.value(), common.layer);
    if let EntityType::Insert(insert) = entity {
        let Some(block) = doc.block_records.get(&insert.block_name) else {
            out.warnings.push(format!("Bloco ausente: {}", insert.block_name)); return;
        };
        if block.flags.is_xref || block.flags.is_xref_overlay || block.flags.is_external {
            out.warnings.push(format!("Xref nao carregada: {}. Adicione o DWG referenciado separadamente.", insert.block_name)); return;
        }
        if insert.row_count > 1 || insert.column_count > 1 {
            out.warnings.push(format!("MINSERT nao suportado: {}", name)); return;
        }
        let b = block.base_point;
        let world = matrix * insert.get_transform().matrix * Matrix4::translation(-b.x, -b.y, -b.z);
        for child in doc.entities_in_block(&insert.block_name) {
            walk(doc, child, world, &format!("{}{}/", prefix, insert.block_name), depth+1, out);
        }
        return;
    }
    let sat = match entity {
        EntityType::Solid3D(s) => s.acis_data.parse(),
        EntityType::Region(s) => s.acis_data.parse(),
        EntityType::Body(s) => s.acis_data.parse(),
        EntityType::Surface(s) => s.acis_data.parse(),
        _ => { *out.skipped.entry(entity.as_entity().entity_type().to_string()).or_default() += 1; return; }
    };
    let Some(sat) = sat else { out.warnings.push(format!("ACIS ilegivel: {}", name)); return; };
    let (bodies, loss) = acis::lift(&sat);
    if !loss.is_empty() { out.warnings.push(format!("ACIS incompleto: {}: {:?}", name, loss)); }
    if bodies.is_empty() { out.warnings.push(format!("Nenhum corpo reconstruido: {}", name)); }
    for (index, body) in bodies.iter().enumerate() {
        let tess = mesh::tessellate(body, mesh::TessellationTolerance::new(0.15, 1e-6));
        if !tess.missing_faces.is_empty() {
            out.warnings.push(format!("{}: {} faces nao reconstruidas", name, tess.missing_faces.len()));
        }
        let points = tess.mesh.positions.iter().map(|p| {
            let p = matrix.transform_point(Vector3::new(p[0],p[1],p[2])); [p.x,p.y,p.z]
        }).collect::<Vec<_>>();
        let faces = tess.mesh.triangles.iter().flat_map(|t| [3, t[0] as usize,t[1] as usize,t[2] as usize]).collect::<Vec<_>>();
        if !faces.is_empty() { out.meshes.push(Mesh { name: format!("{} #{}", name,index+1), points, faces }); }
    }
}

fn fixture(path: &str) -> Result<(), Box<dyn std::error::Error>> {
    use acadrust::entities::acis::primitives;
    let mut doc = CadDocument::new();
    doc.header.insertion_units = 4;
    let mut s = Solid3D::new();
    s.set_sat_document(&primitives::build_box([10000.,20000.,3000.], 1000.,2000.,3000.));
    doc.add_entity(EntityType::Solid3D(s))?;
    let mut s = Solid3D::new();
    s.set_sat_document(&primitives::build_cylinder([13000.,20000.,0.], 500.,2000.));
    doc.add_entity(EntityType::Solid3D(s))?;
    DwgWriter::write_to_file(path, &doc)?;
    Ok(())
}

fn run() -> Result<(), Box<dyn std::error::Error>> {
    let args: Vec<String> = std::env::args().collect();
    if args.len() != 3 { return Err("Uso: plantview-dwg entrada.dwg geometria.json | --fixture exemplo.dwg".into()); }
    if args[1] == "--fixture" { return fixture(&args[2]); }
    let mut reader = DwgReader::from_file(&args[1])?;
    let doc = reader.read()?;
    let mut out = Output { units: doc.header.insertion_units, ..Output::default() };
    for entity in doc.model_space_entities() {
        walk(&doc, entity, Matrix4::identity(), "", 0, &mut out);
    }
    for (kind,count) in &out.skipped { out.warnings.push(format!("{} entidade(s) {} ignorada(s)",count,kind)); }
    serde_json::to_writer(BufWriter::new(File::create(&args[2])?), &out)?;
    Ok(())
}
fn main() {
    if let Err(error) = run() { eprintln!("{}", error); std::process::exit(1); }
}
