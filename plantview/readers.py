"""Readers return geometry in metres, preserving world placement."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from collections import Counter
import numpy as np
import pyvista as pv

UNITS = {1: .0254, 2: .3048, 4: .001, 5: .01, 6: 1., 7: 1000.}

def engine_path():
    root = Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parents[1]))
    return root / 'engine' / 'plantview-dwg.exe'

def read_dwg(path, unit_scale=.001):
    engine = engine_path()
    if not engine.is_file():
        raise ValueError('Motor plantview-dwg.exe ausente. Reextraia o pacote completo ou compile dwg-reader.')
    with tempfile.TemporaryDirectory(prefix='PlantView-') as folder:
        root = Path(folder)
        result = root / 'geometry.json'
        proc = subprocess.run([str(engine), str(Path(path).resolve()), str(result)],
                              cwd=folder, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                              timeout=240, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        if proc.returncode != 0 or not result.exists():
            detail = proc.stdout.decode(errors='replace')[-2500:]
            raise ValueError('Falha no leitor DWG experimental. O original não foi alterado.\n' + detail)
        data = json.loads(result.read_text(encoding='utf-8-sig'))
    scale = UNITS.get(data['units'], unit_scale)
    warnings = list(data['warnings'])
    warnings.insert(0, 'DWG experimental: sólidos ACIS suportados pelo motor livre. Xrefs, objetos proxy, MINSERT e objetos especializados podem faltar. Verifique a maquete.')
    if data['units'] not in UNITS:
        warnings.append(f'Unidade DWG não reconhecida ({data["units"]}); aplicada escala {scale} m/unidade.')
    parts = [(m['name'], pv.PolyData(np.asarray(m['points'], dtype=float)*scale, m['faces'])) for m in data['meshes'] if m['points']]
    return parts, warnings

def read_model(path, unit_scale=.001):
    path = Path(path)
    ext = path.suffix.lower()
    warnings = []
    if ext == '.dwg':
        parts, warnings = read_dwg(path, unit_scale)
    elif ext in ('.step', '.stp'):
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
        parts = [(path.stem, pv.PolyData(np.asarray(points), faces))] if points else []
    elif ext == '.ifc':
        import ifcopenshell
        import ifcopenshell.geom
        doc = ifcopenshell.open(str(path))
        settings = ifcopenshell.geom.settings()
        settings.set(settings.USE_WORLD_COORDS, True)
        parts = []
        for entity in doc.by_type('IfcProduct'):
            if not entity.Representation: continue
            try:
                shape = ifcopenshell.geom.create_shape(settings, entity)
                points = np.array(shape.geometry.verts).reshape(-1, 3)
                triangles = np.array(shape.geometry.faces).reshape(-1, 3)
                faces = np.column_stack((np.full(len(triangles), 3), triangles)).ravel()
                if len(points): parts.append((f'{entity.Name or entity.is_a()} | {entity.GlobalId}', pv.PolyData(points, faces)))
            except Exception as error:
                warnings.append(f'{entity.GlobalId}: {error}')
    elif ext == '.dxf':
        import ezdxf
        from ezdxf.disassemble import recursive_decompose
        from ezdxf.path import make_path
        doc = ezdxf.readfile(path)
        unit = int(doc.header.get('$INSUNITS', 0))
        scale = UNITS.get(unit, unit_scale)
        if unit not in UNITS: warnings.append(f'Unidade DXF não reconhecida; escala {scale} m/unidade.')
        parts = []
        skipped = Counter()
        for entity in recursive_decompose(doc.modelspace()):
            kind = entity.dxftype()
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
                parts.append((f'{entity.dxf.layer} | {kind}', mesh))
            except Exception: skipped[kind] += 1
        warnings.extend(f'{count} entidade(s) {kind} não suportada(s).' for kind, count in skipped.items())
    elif ext in ('.stl', '.obj', '.ply', '.vtp'):
        mesh = pv.read(str(path))
        mesh.points *= unit_scale
        parts = [(path.stem, mesh)]
        warnings.append(f'Malha sem unidade: escala aplicada {unit_scale} m/unidade.')
    else:
        raise ValueError(f'Formato {ext} não suportado. NWC/NWD/RVT exigem SDK específico.')
    if not parts:
        raise ValueError('Nenhuma geometria compatível encontrada.\n' + '\n'.join(warnings[:30]))
    return parts, warnings
