"""Mouse-only first-person viewpoint, no CAD orbital pivot.

Left drag: rotate camera in place (yaw/pitch).
Middle drag: camera pan. Scroll: dolly forward/back in viewing direction.
Shift: increase sensitivity/speed. No WASD bindings.
"""
import math
import vtk


class MouseLookStyle(vtk.vtkInteractorStyleUser):
    def __init__(self):
        super().__init__()
        self.drag_mode = None
        self.previous = None
        self.AddObserver('LeftButtonPressEvent', self.left_down)
        self.AddObserver('LeftButtonReleaseEvent', self.release)
        self.AddObserver('MiddleButtonPressEvent', self.middle_down)
        self.AddObserver('MiddleButtonReleaseEvent', self.release)
        self.AddObserver('MouseMoveEvent', self.move)
        self.AddObserver('MouseWheelForwardEvent', lambda o,e: self.dolly(1))
        self.AddObserver('MouseWheelBackwardEvent', lambda o,e: self.dolly(-1))

    def camera(self):
        renderer = self.GetCurrentRenderer() or self.GetInteractor().GetRenderWindow().GetRenderers().GetFirstRenderer()
        return renderer.GetActiveCamera(), renderer

    def left_down(self, obj, event):
        self.drag_mode, self.previous = 'look', self.GetInteractor().GetEventPosition()

    def middle_down(self, obj, event):
        self.drag_mode, self.previous = 'pan', self.GetInteractor().GetEventPosition()

    def release(self, obj, event):
        self.drag_mode, self.previous = None, None

    def move(self, obj, event):
        pos = self.GetInteractor().GetEventPosition()
        if self.drag_mode is None or self.previous is None: return
        dx, dy = pos[0]-self.previous[0], pos[1]-self.previous[1]
        self.previous = pos
        if not (dx or dy): return
        camera, renderer = self.camera()
        speed = 2.5 if self.GetInteractor().GetShiftKey() else 1.0
        if self.drag_mode == 'look':
            # Azimuth/Elevation rotate about focal point, so preserve eye position
            # by translating focal point after camera rotations.
            import numpy as np
            eye = np.array(camera.GetPosition())
            camera.Azimuth(-dx * .20 * speed)
            camera.Elevation(-dy * .20 * speed)
            camera.OrthogonalizeViewUp()
            displacement = eye - np.array(camera.GetPosition())
            camera.SetPosition(*eye)
            camera.SetFocalPoint(*(np.array(camera.GetFocalPoint()) + displacement))
        else:
            import numpy as np
            eye = np.array(camera.GetPosition())
            focal = np.array(camera.GetFocalPoint())
            direction = focal-eye
            dist = max(np.linalg.norm(direction), .01)
            direction /= dist
            up = np.array(camera.GetViewUp()); up /= max(np.linalg.norm(up),1e-12)
            right = np.cross(direction,up); right /= max(np.linalg.norm(right),1e-12)
            height = max(self.GetInteractor().GetRenderWindow().GetSize()[1],1)
            step = 2*dist*math.tan(math.radians(camera.GetViewAngle())/2)/height
            offset = (-dx*right-dy*up)*step*speed
            camera.SetPosition(*(eye+offset)); camera.SetFocalPoint(*(focal+offset))
        renderer.ResetCameraClippingRange()
        self.GetInteractor().Render()

    def dolly(self, direction):
        import numpy as np
        camera, renderer = self.camera()
        eye = np.array(camera.GetPosition()); focal = np.array(camera.GetFocalPoint())
        view = focal-eye; dist = np.linalg.norm(view)
        if dist < 1e-10: return
        speed = 3 if self.GetInteractor().GetShiftKey() else 1
        movement = view/dist * (dist*.15*speed*direction)
        camera.SetPosition(*(eye+movement)); camera.SetFocalPoint(*(focal+movement))
        renderer.ResetCameraClippingRange()
        self.GetInteractor().Render()
