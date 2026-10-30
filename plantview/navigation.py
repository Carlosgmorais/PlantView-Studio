"""Autodesk Navisworks Manage navigation style for VTK.

Controles Navisworks:
- Botão esquerdo arrastar: Olhar ao redor livremente (Look Around em primeira pessoa, gira no próprio eixo).
- Botão do meio (scroll pressionado) arrastar: Pan suave (deslocamento lateral e vertical).
- Shift + Botão do meio (scroll pressionado) arrastar: Ferramenta Orbital (Orbit clássico do Navisworks em torno do ponto de interesse).
- Scroll (rodinha): Avançar / recuar (zoom suave na direção da visão).
- Shift + qualquer movimento: Aumenta a velocidade de navegação.
- Sem movimentação WASD.
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
        self.drag_mode = 'look'
        if interactor and interactor.GetRenderWindow():
            interactor.GetRenderWindow().SetDesiredUpdateRate(30.0)

    def middle_down(self, obj, event):
        interactor = self.GetInteractor()
        self.previous = interactor.GetEventPosition()
        if interactor and interactor.GetRenderWindow():
            interactor.GetRenderWindow().SetCurrentCursor(9)
            interactor.GetRenderWindow().SetDesiredUpdateRate(30.0)
        if interactor.GetShiftKey():
            self.drag_mode = 'orbit'
        else:
            self.drag_mode = 'pan'

    def right_down(self, obj, event):
        interactor = self.GetInteractor()
        self.previous = interactor.GetEventPosition()
        self.drag_mode = 'look'
        if interactor and interactor.GetRenderWindow():
            interactor.GetRenderWindow().SetDesiredUpdateRate(30.0)

    def mouse_up(self, obj, event):
        self.drag_mode = None
        self.previous = None
        interactor = self.GetInteractor()
        if interactor and interactor.GetRenderWindow():
            interactor.GetRenderWindow().SetCurrentCursor(0)
            interactor.GetRenderWindow().SetDesiredUpdateRate(0.001)
            interactor.Render()

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

        # Sensitivity speed multiplier (Shift accelerates navigation)
        speed = 2.5 if interactor.GetShiftKey() else 1.0

        if self.drag_mode == 'look':
            # Autodesk Navisworks First-Person Look Around:
            # - Eye stays strictly locked at its current 3D position (no orbit, no translation)
            # - Left/Right mouse moves rotate Yaw around global Z-up axis [0, 0, 1]
            # - Up/Down mouse moves rotate Pitch around local camera Right axis
            # - Pitch is clamped to prevent flipping or horizon inversion
            # - Horizon never tilts (ViewUp is maintained upright)
            eye = np.array(camera.GetPosition(), dtype=float)
            focal = np.array(camera.GetFocalPoint(), dtype=float)
            view_vec = focal - eye
            dist = np.linalg.norm(view_vec)
            if dist < 1e-6:
                dist = 1.0
                view_vec = np.array([1.0, 0.0, 0.0])

            horiz_dist = np.hypot(view_vec[0], view_vec[1])
            yaw = math.atan2(view_vec[1], view_vec[0])
            pitch = math.atan2(view_vec[2], max(horiz_dist, 1e-9))

            sens = 0.004 * speed
            yaw -= dx * sens
            pitch = np.clip(pitch + dy * sens, -math.radians(88.5), math.radians(88.5))

            cos_pitch = math.cos(pitch)
            new_dir = np.array([
                cos_pitch * math.cos(yaw),
                cos_pitch * math.sin(yaw),
                math.sin(pitch)
            ], dtype=float)

            camera.SetPosition(*eye)
            camera.SetFocalPoint(*(eye + new_dir * dist))
            camera.SetViewUp(0.0, 0.0, 1.0)

        elif self.drag_mode == 'orbit':
            # Autodesk Navisworks Orbit Tool:
            # - Rotates the camera around the focal point preserving Z-up upright horizon
            eye = np.array(camera.GetPosition(), dtype=float)
            focal = np.array(camera.GetFocalPoint(), dtype=float)
            view_vec = eye - focal
            dist = np.linalg.norm(view_vec)
            if dist < 1e-6:
                dist = 1.0
                view_vec = np.array([1.0, 0.0, 0.0])

            horiz_dist = np.hypot(view_vec[0], view_vec[1])
            yaw = math.atan2(view_vec[1], view_vec[0])
            pitch = math.atan2(view_vec[2], max(horiz_dist, 1e-9))

            sens = 0.005 * speed
            yaw += dx * sens
            pitch = np.clip(pitch - dy * sens, -math.radians(88.5), math.radians(88.5))

            cos_pitch = math.cos(pitch)
            new_offset = np.array([
                cos_pitch * math.cos(yaw),
                cos_pitch * math.sin(yaw),
                math.sin(pitch)
            ], dtype=float) * dist

            camera.SetPosition(*(focal + new_offset))
            camera.SetFocalPoint(*focal)
            camera.SetViewUp(0.0, 0.0, 1.0)

        elif self.drag_mode == 'pan':
            # Navisworks Pan: smooth lateral and vertical translation
            eye = np.array(camera.GetPosition(), dtype=float)
            focal = np.array(camera.GetFocalPoint(), dtype=float)
            view_vec = focal - eye
            dist = max(np.linalg.norm(view_vec), 0.01)
            direction = view_vec / dist

            up = np.array(camera.GetViewUp(), dtype=float)
            if np.linalg.norm(up) < 1e-6:
                up = np.array([0.0, 0.0, 1.0])
            else:
                up = up / np.linalg.norm(up)

            right = np.cross(direction, up)
            if np.linalg.norm(right) < 1e-6:
                right = np.array([1.0, 0.0, 0.0])
            else:
                right = right / np.linalg.norm(right)

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

        eye = np.array(camera.GetPosition(), dtype=float)
        focal = np.array(camera.GetFocalPoint(), dtype=float)
        view = focal - eye
        dist = np.linalg.norm(view)
        if dist < 1e-9:
            return

        interactor = self.GetInteractor()
        speed = 2.5 if interactor and interactor.GetShiftKey() else 1.0
        
        # Smooth navigation: move along viewing direction with proportional step
        step = max(dist * 0.15 * speed, 0.05) * direction
        movement = (view / dist) * step
        
        camera.SetPosition(*(eye + movement))
        camera.SetFocalPoint(*(focal + movement))
        renderer.ResetCameraClippingRange()
        interactor.Render()
        if self.on_change:
            self.on_change(camera)
