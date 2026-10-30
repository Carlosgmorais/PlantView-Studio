"""Headless unit tests of GPU instancing decisions, no Qt/PyVista needed."""
import sys, types, unittest
from pathlib import Path
import numpy as np
qt = types.ModuleType('PySide6'); qt.QtGui=types.SimpleNamespace()
sys.modules.setdefault('PySide6',qt)
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from plantview.gpu import geometry_fingerprint, add_optimized_parts

class Mesh:
    def __init__(self, shift=(0,0,0), rgb=(255,0,0), changed=False):
        self.points=np.array([[0,0,0],[1,0,0],[0,1,0]],float)+np.array(shift)
        if changed: self.points[1,0]+=0.1
        self.faces=np.array([3,0,1,2],dtype=np.int64)
        self.n_cells=1
        self.field_data={'plantview_rgb':np.array([rgb])}
    def copy(self,deep=True):
        m=Mesh();m.points=self.points.copy();m.faces=self.faces.copy();m.field_data=self.field_data.copy();return m
class Actor:
    def SetVisibility(self,v):self.visible=v
    def GetMapper(self):return types.SimpleNamespace(SetStatic=lambda x:None,SetScalarVisibility=lambda x:None)
    def GetProperty(self):return types.SimpleNamespace(SetInterpolationToFlat=lambda:None,SetEdgeVisibility=lambda x:None)
class Plot:
    def __init__(self): self.calls=[]
    def add_mesh(self, mesh, **kwargs):self.calls.append(kwargs);return Actor()
class Tests(unittest.TestCase):
    def test_translation_identical(self):
        a,b=Mesh(),Mesh((12345,7,-3))
        self.assertEqual(geometry_fingerprint(a)[0],geometry_fingerprint(b)[0])
    def test_different_geom(self):
        self.assertNotEqual(geometry_fingerprint(Mesh())[0],geometry_fingerprint(Mesh(changed=True))[0])
    def test_color_separation(self):
        import plantview.gpu as gpu
        old=gpu.make_instance_actor
        calls=[]
        def fake(plot,source,origins,color): calls.append((len(origins),color));return Actor()
        gpu.make_instance_actor=fake
        try:
            parts=[('a',Mesh((i,0,0))) for i in range(5)]+[('blue',Mesh((10,0,0),rgb=(0,0,255)))]
            actors,names,stats=add_optimized_parts(Plot(),parts,False)
            self.assertEqual(stats,dict(original_parts=6,gpu_actors=2,instance_groups=1,instanced_parts=5))
            self.assertEqual(calls[0],(5,(1.,0.,0.)))
            self.assertFalse(actors[0].visible)
        finally:gpu.make_instance_actor=old
if __name__=='__main__':unittest.main(verbosity=2)
