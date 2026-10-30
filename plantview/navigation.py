"""Autodesk Navisworks Manage navigation style for VTK.

Controles Navisworks:
- Bot�o esquerdo arrastar: Olhar ao redor livremente (Look Around em primeira pessoa, gira no pr�prio eixo).
- Bot�o do meio (scroll pressionado) arrastar: Pan suave (deslocamento lateral e vertical).
- Shift + Bot�o do meio (scroll pressionado) arrastar: Ferramenta Orbital (Orbit cl�ssico do Navisworks em torno do ponto de interesse).
- Scroll (rodinha): Avan�ar / recuar (zoom suave na dire��o da vis�o).
- Shift + qualquer movimento: Aumenta a velocidade de navega��o.
- Sem movimenta��o WASD.
- F5: Atalho para atualizar modelos.
"""
import math
import numpy as np
import vtk


class NavisworksStyle(vtk.vtkInteractorStyleUser):
    def __init__(self, on_change=None, on_refresh=None):
        super().__init__()
        self.drag_mode = None
        self.previous = None
        self.on_change = on_change
        self.on_refresh = on_refresh
        
        # Event observers
        self.AddObserver('LeftButtonPressEvent', self.left_down)
        self.AddObserver('LeftButtonReleaseEvent', self.mouse_up)
        self.AddObserver('MiddleButtonPressEvent', self.middle_down)
        self.AddObserver('MiddleButtonReleaseEvent', self.mouse_up)
        self.AddObserver('RightButtonPressEvent', self.right_down)
        self.AddObserver('RightButtonReleaseEvent', self.mouse_up)
        self.AddObserver('MouseMoveEvent', self.mouse_move)
        self.AddObserver('MouseWheelForwardEvent', lambda o, e: self.dolly(1))
        self.AddObserver('MouseWheelBackwardEvent', lambda o, e: self.dolly(-1))
        self.AddObserver('KeyPressEvent', self.key_press)

    def camera(self):
        interactor = self.GetInteractor()
        if not interactor:
            return None, None
        rw = interactor.GetRenderWindow()
        if not rw:
            return None, None
        renderers = rw.GetRenderers()
        renderer = self.GetCurrentRenderer() or renderers.GetFirstRenderer()
        if not renderer:
            return None, None
        camera = renderer.GetActiveCamera()
        camera.ParallelProjectionOff()
        return camera, renderer

    def left_down(self, obj, event):
        interactor = self.GetInteractor()
        self.previous = interactor.GetEventPosition()
        # Left drag is first-person look-around (rotating camera in place)
        self.drag_mode = 'look'

    def middle_down(self, obj, event):
        interactor = self.GetInteractor()
        self.previous = interactor.GetEventPosition()
        # If Shift is held: Navisworks Orbit Tool!
        # If Shift is not held: Navisworks Pan Tool!
        interactor.GetRenderWindow().SetCurrentCursor(9)
        if interactor.GetShiftKey():
            self.drag_mode = 'orbit'
        else:
            self.drag_mode = 'pan'

    def right_down(self, obj, event):
        interactor = self.GetInteractor()
        self.previous = interactor.GetEventPosition()
        self.drag_mode = 'look'

    def mouse_up(self, obj, event):
        self.drag_mode = None
        self.previous = None
        if self.GetInteractor():
            self.GetInteractor().GetRenderWindow().SetCurrentCursor(0)

    def key_press(self, obj, event):
        interactor = self.GetInteractor()
        key = interactor.GetKeySym()
        if key == 'F5' and self.on_refresh:
            self.on_refresh()

    def mouse_move(self, obj, event):
        if self.drag_mode is None or self.previous is None:
            return
        interactor = self.GetInteractor()
        pos = interactor.GetEventPosition()
        dx = pos[0] - self.previous[0]
        dy = pos[1] - self.previous[1]
        self.previous = pos
        if dx == 0 and dy == 0:
            return

        camera, renderer = self.camera()
        if not camera or not renderer:
            return

        # Sensitivity speed multiplier
        speed = 1.0

        if self.drag_mode == 'look':
            # Look around freely: camera rotates in place without changing its eye position
            eye = np.array(camera.GetPosition())
            camera.Azimuth(-dx * 0.22 * speed)
            camera.Elevation(-dy * 0.22 * speed)
            camera.OrthogonalizeViewUp()
            
            # Restore eye position by offsetting focal point
            disp = eye - np.array(camera.GetPosition())
            camera.SetPosition(*eye)
            camera.SetFocalPoint(*(np.array(camera.GetFocalPoint()) + disp))

        elif self.drag_mode == 'orbit':
            # Navisworks Orbit Tool: rotates camera around the focal point / center of interest
            camera.Azimuth(-dx * 0.35 * speed)
            camera.Elevation(-dy * 0.35 * speed)
            camera.OrthogonalizeViewUp()

        elif self.drag_mode == 'pan':
            # Pan: smooth lateral and vertical translation
            eye = np.array(camera.GetPosition())
            focal = np.array(camera.GetFocalPoint())
            view_vec = focal - eye
            dist = max(np.linalg.norm(view_vec), 0.01)
            direction = view_vec / dist
            
            up = np.array(camera.GetViewUp())
            up_norm = np.linalg.norm(up)
            if up_norm > 1e-12:
                up = up / up_norm
            else:
                up = np.array([0.0, 0.0, 1.0])
                
            right = np.cross(direction, up)
            right_norm = np.linalg.norm(right)
            if right_norm > 1e-12:
                right = right / right_norm
            else:
                right = np.array([1.0, 0.0, 0.0])

            rw_size = interactor.GetRenderWindow().GetSize()
            height = max(rw_size[1], 1)
            step = 2.0 * dist * math.tan(math.radians(camera.GetViewAngle()) / 2.0) / height
            offset = (-dx * right - dy * up) * step * speed
            
            camera.SetPosition(*(eye + offset))
            camera.SetFocalPoint(*(focal + offset))

        renderer.ResetCameraClippingRange()
        interactor.Render()
        if self.on_change:
            self.on_change(camera)

    def dolly(self, direction):
        """Scroll wheel navigation: smooth movement in camera viewing direction."""
        camera, renderer = self.camera()
        if not camera or not renderer:
            return

        eye = np.array(camera.GetPosition())
        focal = np.array(camera.GetFocalPoint())
        view = focal - eye
        dist = np.linalg.norm(view)
        if dist < 1e-9:
            return

        interactor = self.GetInteractor()
        speed = 3.5 if interactor and interactor.GetShiftKey() else 1.0
        
        # Smooth step: proportional to distance, minimum 0.5m for responsiveness
        step = max(dist * 0.16 * speed, 1e-6) * direction
        movement = (view / dist) * step
        
        camera.SetPosition(*(eye + movement))
        camera.SetFocalPoint(*(focal + movement))
        renderer.ResetCameraClippingRange()
        interactor.Render()
        if self.on_change:
            self.on_change(camera)
