"""Generate small original examples, not user CAD files."""
from pathlib import Path
import sys
import subprocess
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from plantview.readers import engine_path
from plantview.project import save_project
import cadquery as cq
import numpy as np
import ifcopenshell.api

folder = ROOT/'examples'
folder.mkdir(exist_ok=True)
subprocess.run([str(engine_path()), '--fixture', str(folder/'equipamentos.dwg')],check=True)
frame = cq.Workplane().box(7000,5000,200).translate((11000,20000,0))
for x in (8000,14000):
    for y in (18000,22000):
        frame = frame.union(cq.Workplane().box(200,200,4500).translate((x,y,2250)))
frame = frame.union(cq.Workplane().box(6200,200,200).translate((11000,18000,4500)))
frame = frame.union(cq.Workplane().box(6200,200,200).translate((11000,22000,4500)))
cq.exporters.export(frame,str(folder/'estrutura.step'))
api = ifcopenshell.api.run
f = api('project.create_file')
api('root.create_entity',f,ifc_class='IfcProject',name='PlantView exemplo')
api('unit.assign_unit',f)
context = api('context.add_context',f,context_type='Model')
body = api('context.add_context',f,context_type='Model',context_identifier='Body',target_view='MODEL_VIEW',parent=context)
wall = api('root.create_entity',f,ifc_class='IfcWall',name='Parede de exemplo')
rep = api('geometry.add_wall_representation',f,context=body,length=7.,height=1.2,thickness=.2)
api('geometry.assign_representation',f,product=wall,representation=rep)
matrix=np.eye(4); matrix[:3,3]=[7.5,22.5,0]
api('geometry.edit_object_placement',f,product=wall,matrix=matrix)
f.write(str(folder/'parede.ifc'))
save_project(folder/'Demonstracao.pvproj',[{'path':str(folder/name),'visible':True,'scale':.001} for name in ('equipamentos.dwg','estrutura.step','parede.ifc')],None)
print('Examples created:',folder)
