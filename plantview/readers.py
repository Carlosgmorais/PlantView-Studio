"""Readers return geometry in metres, preserving world placement and original CAD colors."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from collections import Counter
from typing import List, Tuple, Callable, Optional
import numpy as np
import pyvista as pv
from .colors import resolve_layer_color, resolve_ifc_color, ACI_TABLE

UNITS = {1: .0254, 2: .3048, 4: .001, 5: .01, 6: 1., 7: 1000.}

def engine_path():
    root = Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parents[1]))
    # Check root/engine or local engine
    cand = root / 'engine' / 'plantview-dwg.exe'
    if cand.is_file():
        return cand
    cand2 = Path(__file__).resolve().parents[1] / 'engine' / 'plantview-dwg.exe'
    if cand2.is_file():
        return cand2
    return cand

def parse_dwg_mesh_info(name: str) -> Tuple[str, str, str]:
    """Parse prefix, handle, and layer from mesh name.
    Examples:
      '31 | 0 #1' -> ('', '31', '0')
      'VALVE/4B | PIPING #2' -> ('VALVE/', '4B', 'PIPING')
    """
    block_prefix = ''
    layer_name = '0'
    handle = ''
    if ' | ' in name:
        left, right = name.split(' | ', 1)
        layer_name = right.split('#')[0].strip()
        if '/' in left:
            block_prefix, handle = left.rsplit('/', 1)
            block_prefix += '/'
        else:
            handle = left.strip()
    else:
        handle = name
    return block_prefix, handle, layer_name

def read_dwg(path, unit_scale=.001, progress_callback: Optional[Callable[[float, str], bool]] = None):
    engine = engine_path()
    if not engine.is_file():
        raise ValueError(f'Motor plantview-dwg.exe ausente em {engine}. Reextraia o pacote completo ou verifique a pasta engine.')
    
    if progress_callback:
        progress_callback(10.0, f'Iniciando leitura DWG: {Path(path).name}...')

    with tempfile.TemporaryDirectory(prefix='PlantView-') as folder:
        root = Path(folder)
        result = root / 'geometry.json'
        
        if progress_callback:
            progress_callback(25.0, 'Decodificando entidades ACIS (3DSOLID, BODY, REGION)...')
            
        proc = subprocess.run([str(engine), str(Path(path).resolve()), str(result)],
                              cwd=folder, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                              timeout=300, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        if proc.returncode != 0 or not result.exists():
            detail = proc.stdout.decode(errors='replace')[-2500:]
            raise ValueError('Falha no leitor DWG experimental. O original não foi alterado.\n' + detail)
            
        if progress_callback:
            progress_callback(60.0, 'Processando malha e coordenadas...')
            
        data = json.loads(result.read_text(encoding='utf-8-sig'))

    scale = UNITS.get(data['units'], unit_scale)
    warnings = list(data.get('warnings', []))
    warnings.insert(0, 'DWG: sólidos ACIS lidos pelo motor nativo. Coordenadas mundiais reais preservadas.')
    if data['units'] not in UNITS:
        warnings.append(f'Unidade DWG não reconhecida ({data["units"]}); aplicada escala {scale} m/unidade.')

    parts = []
    meshes = data.get('meshes', [])
    total_meshes = len(meshes)
    
    for i, m in enumerate(meshes):
        if not m['points']:
            continue
        mesh = pv.PolyData(np.asarray(m['points'], dtype=float) * scale, m['faces'])
        
        # Color resolution:
        # 1. Use explicit mesh color if provided and not default placeholder
        # 2. Resolve via layer name according to AutoCAD standards
        _, _, layer_name = parse_dwg_mesh_info(m['name'])
        raw_color = m.get('color')
        
        if raw_color and raw_color != [190, 201, 212] and raw_color != [230, 230, 230]:
            color_rgb = raw_color
        else:
            color_rgb = list(resolve_layer_color(layer_name))
            
        mesh.field_data['plantview_rgb'] = np.array([color_rgb], dtype=np.uint8)
        mesh.field_data['plantview_layer'] = np.array([layer_name])
        parts.append((m['name'], mesh))
        
        if progress_callback and i % max(1, total_meshes // 10) == 0:
            pct = 60.0 + (35.0 * i / max(1, total_meshes))
            progress_callback(pct, f'Criando atores gráficos ({i}/{total_meshes})...')

    if progress_callback:
        progress_callback(100.0, 'Modelo DWG carregado com sucesso.')

    return parts, warnings

def read_model(path, unit_scale=.001, progress_callback: Optional[Callable[[float, str], bool]] = None):
    path = Path(path)
    ext = path.suffix.lower()
    warnings = []
    
    if ext == '.dwg':
        parts, warnings = read_dwg(path, unit_scale, progress_callback)
    elif ext in ('.step', '.stp'):
        if progress_callback:
            progress_callback(15.0, f'Lendo modelo STEP: {path.name}...')
        from OCP.STEPControl import STEPControl_Reader
        from OCP.IFSelect import IFSelect_RetDone
        from OCP.BRepMesh import BRepMesh_IncrementalMesh
        from OCP.BRep import BRep_Tool
        from OCP.TopExp import TopExp_Explorer
        from OCP.TopAbs import TopAbs_FACE, TopAbs_REVERSED
        from OCP.TopoDS import TopoDS
        from OCP.TopLoc import TopLoc_Location
        reader = STEPControl_Reader()
        if reader.ReadFile(str(path)) != IFSelect_RetDone:
            raise ValueError('Não foi possível ler o STEP.')
        reader.TransferRoots()
        shape = reader.OneShape()
        if progress_callback:
            progress_callback(50.0, 'Triangulando superfícies B-Rep...')
        BRepMesh_IncrementalMesh(shape, .5, False, .3, True)
        explorer = TopExp_Explorer(shape, TopAbs_FACE)
        points, faces = [], []
        while explorer.More():
            face = TopoDS.Face_s(explorer.Current())
            loc = TopLoc_Location()
            triangulation = BRep_Tool.Triangulation_s(face, loc)
            if triangulation is not None:
                base = len(points)
                for i in range(1, triangulation.NbNodes()+1):
                    p = triangulation.Node(i).Transformed(loc.Transformation())
                    points.append([p.X()*.001, p.Y()*.001, p.Z()*.001])
                for i in range(1, triangulation.NbTriangles()+1):
                    a,b,c = triangulation.Triangle(i).Get()
                    if face.Orientation() == TopAbs_REVERSED: b,c = c,b
                    faces.extend([3,base+a-1,base+b-1,base+c-1])
            else: warnings.append('Face STEP sem triangulação.')
            explorer.Next()
        
        parts = []
        if points:
            mesh = pv.PolyData(np.asarray(points), faces)
            # Default metallic steel blue for STEP engineering models
            layer = 'ESTRUTURA' if 'ESTRUTURA' in path.stem.upper() else 'EQUIP'
            color = resolve_layer_color(layer)
            mesh.field_data['plantview_rgb'] = np.array([color], dtype=np.uint8)
            mesh.field_data['plantview_layer'] = np.array([layer])
            parts.append((path.stem, mesh))
        if progress_callback:
            progress_callback(100.0, 'Modelo STEP carregado com sucesso.')
    elif ext == '.ifc':
        if progress_callback:
            progress_callback(15.0, f'Lendo arquivo BIM IFC: {path.name}...')
        import ifcopenshell
        import ifcopenshell.geom
        doc = ifcopenshell.open(str(path))
        settings = ifcopenshell.geom.settings()
        settings.set(settings.USE_WORLD_COORDS, True)
        parts = []
        products = list(doc.by_type('IfcProduct'))
        total_p = len(products)
        for idx, entity in enumerate(products):
            if not entity.Representation: continue
            try:
                shape = ifcopenshell.geom.create_shape(settings, entity)
                points = np.array(shape.geometry.verts).reshape(-1, 3)
                triangles = np.array(shape.geometry.faces).reshape(-1, 3)
                faces = np.column_stack((np.full(len(triangles), 3), triangles)).ravel()
                if len(points):
                    mesh = pv.PolyData(points, faces)
                    color = resolve_ifc_color(entity.is_a())
                    mesh.field_data['plantview_rgb'] = np.array([color], dtype=np.uint8)
                    mesh.field_data['plantview_layer'] = np.array([entity.is_a()])
                    parts.append((f'{entity.Name or entity.is_a()} | {entity.GlobalId}', mesh))
            except Exception as error:
                warnings.append(f'{entity.GlobalId}: {error}')
            if progress_callback and idx % max(1, total_p // 10) == 0:
                pct = 20.0 + (75.0 * idx / max(1, total_p))
                progress_callback(pct, f'Processando elementos IFC ({idx}/{total_p})...')
        if progress_callback:
            progress_callback(100.0, 'Modelo IFC carregado com sucesso.')
    elif ext == '.dxf':
        if progress_callback:
            progress_callback(15.0, f'Lendo arquivo DXF: {path.name}...')
        import ezdxf
        from ezdxf.disassemble import recursive_decompose
        from ezdxf.path import make_path
        doc = ezdxf.readfile(path)
        unit = int(doc.header.get('$INSUNITS', 0))
        scale = UNITS.get(unit, unit_scale)
        if unit not in UNITS: warnings.append(f'Unidade DXF não reconhecida; escala {scale} m/unidade.')
        
        # Build layer color table from DXF document
        dxf_layer_colors = {}
        for l in doc.layers:
            # Color is either ACI or true color
            color_idx = l.color
            if color_idx in ACI_TABLE:
                dxf_layer_colors[l.dxf.name] = ACI_TABLE[color_idx]
            else:
                dxf_layer_colors[l.dxf.name] = resolve_layer_color(l.dxf.name)
                
        parts = []
        skipped = Counter()
        for entity in recursive_decompose(doc.modelspace()):
            kind = entity.dxftype()
            layer = entity.dxf.layer
            layer_color = dxf_layer_colors.get(layer, resolve_layer_color(layer))
            try:
                if kind == '3DFACE':
                    pts = np.array([tuple(p) for p in entity.wcs_vertices(close=False)])*scale
                    mesh = pv.PolyData(pts, [len(pts), *range(len(pts))])
                elif kind in ('LINE', 'LWPOLYLINE', 'POLYLINE', 'ARC', 'CIRCLE', 'ELLIPSE', 'SPLINE'):
                    points = np.array([tuple(p) for p in make_path(entity).flattening(.5)])*scale
                    if len(points) < 2: continue
                    mesh = pv.lines_from_points(points)
                else:
                    skipped[kind] += 1; continue
                mesh.field_data['plantview_rgb'] = np.array([layer_color], dtype=np.uint8)
                mesh.field_data['plantview_layer'] = np.array([layer])
                parts.append((f'{layer} | {kind}', mesh))
            except Exception: skipped[kind] += 1
        warnings.extend(f'{count} entidade(s) {kind} não suportada(s).' for kind, count in skipped.items())
        if progress_callback:
            progress_callback(100.0, 'Modelo DXF carregado com sucesso.')
    elif ext in ('.stl', '.obj', '.ply', '.vtp'):
        if progress_callback:
            progress_callback(20.0, f'Carregando malha 3D: {path.name}...')
        mesh = pv.read(str(path))
        mesh.points *= unit_scale
        color = resolve_layer_color(path.stem)
        mesh.field_data['plantview_rgb'] = np.array([color], dtype=np.uint8)
        mesh.field_data['plantview_layer'] = np.array([path.stem])
        parts = [(path.stem, mesh)]
        warnings.append(f'Malha sem unidade: escala aplicada {unit_scale} m/unidade.')
        if progress_callback:
            progress_callback(100.0, 'Malha carregada com sucesso.')
    else:
        raise ValueError(f'Formato {ext} não suportado. NWC/NWD/RVT exigem SDK específico.')
        
    if not parts:
        raise ValueError('Nenhuma geometria compatível encontrada.\n' + '\n'.join(warnings[:30]))
    return parts, warnings
