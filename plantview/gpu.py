"""GPU-oriented VTK renderer configuration and runtime diagnostics.

The renderer needs a working hardware OpenGL context. DWG decoding / ACIS
triangulation remain CPU jobs; no guarantee of hardware acceleration on RDP/VMs.
"""
import os
from PySide6 import QtGui


def configure_surface():
    # Called before QApplication creates its first window/context.
    if os.environ.get('PLANTVIEW_SOFTWARE_RENDER') == '1':
        return
    fmt = QtGui.QSurfaceFormat()
    fmt.setRenderableType(QtGui.QSurfaceFormat.OpenGL)
    fmt.setProfile(QtGui.QSurfaceFormat.CoreProfile)
    fmt.setVersion(3, 2)
    fmt.setDepthBufferSize(24)
    fmt.setStencilBufferSize(8)
    fmt.setSwapBehavior(QtGui.QSurfaceFormat.DoubleBuffer)
    QtGui.QSurfaceFormat.setDefaultFormat(fmt)


def optimize_actor(actor):
    """Explicitly mark meshes immutable for VTK's OpenGL vertex buffer reuse."""
    mapper = actor.GetMapper()
    if mapper is not None:
        mapper.SetStatic(True)
        mapper.SetScalarVisibility(False)  # entity colors provided as actor properties
    prop = actor.GetProperty()
    prop.SetInterpolationToFlat()
    prop.SetEdgeVisibility(False)
    return actor


def gpu_report(plot):
    rw = plot.render_window
    details = ['Backend: VTK OpenGL', f'OpenGL window: {rw.GetClassName()}']
    if hasattr(rw, 'GetOpenGLSupportMessage'):
        try: details.append('Suporte OpenGL: ' + rw.GetOpenGLSupportMessage())
        except Exception: pass
    if hasattr(rw, 'ReportCapabilities'):
        try:
            report = rw.ReportCapabilities()
            for line in str(report).splitlines():
                if any(word in line.lower() for word in ('vendor', 'renderer', 'version', 'opengl')):
                    details.append(line.strip())
        except Exception: pass
    return '\n'.join(dict.fromkeys(details))


def geometry_fingerprint(mesh):
    """Find identical translated tessellations; intentionally excludes rotations/scaling."""
    import hashlib
    import numpy as np
    points = np.asarray(mesh.points, dtype=np.float64)
    if not len(points):
        return None
    origin = points[0].copy()
    relative = np.ascontiguousarray(points - origin)
    topology = np.ascontiguousarray(mesh.faces, dtype=np.int64)
    digest = hashlib.blake2b(digest_size=20)
    digest.update(relative.tobytes())
    digest.update(topology.tobytes())
    return (len(points), int(mesh.n_cells), digest.hexdigest()), origin


def make_instance_actor(plot, source, origins, color):
    """Use VTK GPU glyph mapping for exact repeated geometry in distinct positions."""
    import numpy as np
    import pyvista as pv
    from vtkmodules.vtkRenderingCore import vtkGlyph3DMapper, vtkActor
    cloud = pv.PolyData(np.asarray(origins, dtype=float))
    mapper = vtkGlyph3DMapper()
    mapper.SetInputData(cloud)
    mapper.SetSourceData(source)
    mapper.ScalingOff()
    mapper.OrientOff()
    mapper.SetScalarVisibility(False)
    actor = vtkActor()
    actor.SetMapper(mapper)
    actor.GetProperty().SetColor(*color)
    actor.GetProperty().SetInterpolationToFlat()
    plot.add_actor(actor, reset_camera=False, render=False)
    return actor


def add_optimized_parts(plot, parts, visible=True):
    """Instance same-color translated clones, retain all names in tree.

    Grouping changes actor-level picking: individual instances are not selectable.
    Does not instance rotated/mirrored variants or mismatching vertex ordering.
    """
    from collections import defaultdict
    import numpy as np
    buckets = defaultdict(list)
    for name, mesh in parts:
        color_data = mesh.field_data.get('plantview_rgb')
        color = tuple(int(x)/255. for x in color_data[0]) if color_data is not None else (.74,.79,.83)
        signature = geometry_fingerprint(mesh)
        if signature is None:
            continue
        key, origin = signature
        buckets[(key, color)].append((name, mesh, origin))
    actors, groups, instances = [], 0, 0
    for (_, color), items in buckets.items():
        if len(items) >= 3:
            source = items[0][1].copy(deep=True)
            source.points = np.asarray(source.points) - items[0][2]
            actor = make_instance_actor(plot, source, [origin for _, _, origin in items], color)
            actor.SetVisibility(visible)
            actors.append(actor)
            groups += 1
            instances += len(items)
        else:
            for _, mesh, _ in items:
                actor = plot.add_mesh(mesh, color=color, smooth_shading=False,
                                      reset_camera=False, render=False)
                optimize_actor(actor)
                actor.SetVisibility(visible)
                actors.append(actor)
    return actors, [name for name, _ in parts], dict(
        original_parts=len(parts), gpu_actors=len(actors),
        instance_groups=groups, instanced_parts=instances)
