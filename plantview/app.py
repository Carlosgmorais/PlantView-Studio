import os
os.environ['QT_API'] = 'pyside6'
import sys
import time
from pathlib import Path
import numpy as np
from PySide6 import QtCore, QtGui, QtWidgets as W
from pyvistaqt import QtInteractor
import pyvista as pv

from .readers import read_model, parse_dwg_mesh_info
from .project import load_project, save_project
from .gpu import (
    configure_surface,
    setup_gpu_renderer,
    optimize_actor,
    gpu_report,
    add_optimized_parts,
    get_system_memory_info
)
from .navigation import NavisworksStyle
from .colors import LayerManager, resolve_layer_color
from .icons import create_navis_icon
from .ribbon import NavisRibbonBar
from .loading_dialog import NavisLoadingDialog
from .widgets import NavisCoordinateOverlay, NavisLayerManagerDialog


class ImportWorker(QtCore.QThread):
    loaded = QtCore.Signal(object, object, object)
    failed = QtCore.Signal(str)
    progress = QtCore.Signal(float, str)

    def __init__(self, record):
        super().__init__()
        self.record = record
        self._cancelled = False

    def cancel(self):
        self._cancelled = True

    def run(self):
        try:
            def on_progress(pct: float, msg: str) -> bool:
                if self._cancelled:
                    raise InterruptedError('Carregamento cancelado pelo usuário.')
                self.progress.emit(pct, msg)
                return True

            parts, warnings = read_model(
                self.record['path'],
                unit_scale=self.record.get('scale', 0.001),
                progress_callback=on_progress
            )
            if self._cancelled:
                return
            self.loaded.emit(self.record, parts, warnings)
        except Exception as e:
            self.failed.emit(str(e))


class Window(W.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('PlantView Studio 2026 — Maquete Federada 3D')
        self.setWindowIcon(create_navis_icon('app_logo', 64))
        self.resize(1380, 880)

        self.models = []
        self.queue = []
        self.worker = None
        self.loading_dialog = None
        self.dirty = False
        self.project_path = None
        self.restore_camera = None
        self.measure_points = []
        self.measure_mode = False
        self.total_triangles = 0
        self.layer_manager = LayerManager()
        self.selected_actor = None
        self.fps_counter = 0
        self.fps_last_time = time.time()
        self.current_fps = 60.0

        # Navisworks Manage Application Stylesheet
        self.setStyleSheet("""
            QMainWindow, QWidget {
                background-color: #f0f0f0;
                color: #202020;
                font-family: 'Segoe UI', Tahoma, Arial, sans-serif;
            }
            QTreeWidget {
                background-color: #ffffff;
                border: 1px solid #d0d0d0;
                color: #222222;
                font-size: 11px;
            }
            QTreeWidget::item:selected {
                background-color: #cce8ff;
                color: #000000;
            }
            QPlainTextEdit {
                background-color: #ffffff;
                border: 1px solid #d0d0d0;
                color: #333333;
                font-family: Consolas, monospace;
                font-size: 11px;
            }
            QHeaderView::section {
                background-color: #e5e5e5;
                border: 1px solid #dcdcdc;
                padding: 4px;
                font-weight: 600;
                color: #333333;
            }
            QDockWidget {
                titlebar-close-icon: url(none);
                font-size: 11px;
                font-weight: 600;
            }
            QDockWidget::title {
                background-color: #e2e2e2;
                border: 1px solid #d0d0d0;
                padding: 4px 8px;
            }
            QStatusBar {
                background-color: #e0e0e0;
                border-top: 1px solid #c8c8c8;
                color: #333333;
                font-size: 11px;
            }
        """)

        # Central Widget & Layout
        central = W.QWidget()
        layout = W.QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 2. Viewport Area (Container for 3D View and Floating Overlays)
        viewport_container = W.QWidget()
        vp_layout = W.QStackedLayout(viewport_container)
        vp_layout.setStackingMode(W.QStackedLayout.StackAll)

        self.plot = QtInteractor(viewport_container)
        vp_layout.addWidget(self.plot.interactor)

        # Navisworks Viewport Sky Horizon Gradient
        # Top: Rich sky blue #5b8ecb | Bottom: Pale horizon ice blue #d8e8f8
        self.plot.set_background('#d8e8f8', top='#5b8ecb')
        self.plot.add_axes(interactive=False)

        # Setup GPU Renderer & Hardware Frustum Culling
        setup_gpu_renderer(self.plot)
        self.plot.disable_anti_aliasing()

        # Navisworks Free 3D Navigation
        self.navigation = NavisworksStyle(
            on_change=self.on_camera_changed,
            on_refresh=self.refresh_models
        )
        self.plot.interactor.SetInteractorStyle(self.navigation)

        # Floating Navisworks Coordinate Overlay in bottom-left
        self.coord_overlay = NavisCoordinateOverlay(viewport_container)
        vp_layout.addWidget(self.coord_overlay)

        # 1. Navisworks Ribbon Bar (Created after plot is ready)
        self.ribbon = NavisRibbonBar(self)
        layout.addWidget(self.ribbon)
        layout.addWidget(viewport_container)
        self.setCentralWidget(central)

        # Surface point picking for measurements
        self.plot.enable_surface_point_picking(
            callback=self.point_picked,
            show_message=False,
            show_point=False,
            left_clicking=False
        )

        # Welcome text in 3D scene
        self.plot.add_text(
            'PlantView Studio 2026\nAdicione modelos industriais (DWG • STEP • IFC • DXF)',
            name='welcome',
            font_size=13,
            color='#2a4460'
        )

        # Dock 1: Selection Tree (Left Dock)
        self.tree = W.QTreeWidget()
        self.tree.setHeaderLabels(['Hierarquia de Componentes'])
        self.tree.itemChanged.connect(self.visibility_changed)
        self.tree.itemSelectionChanged.connect(self.selection_changed)
        self.tree_dock = W.QDockWidget('Selection Tree', self)
        self.tree_dock.setWidget(self.tree)
        self.tree_dock.setMinimumWidth(300)
        self.addDockWidget(QtCore.Qt.LeftDockWidgetArea, self.tree_dock)

        # Dock 2: Log and Measurement Report (Bottom Dock)
        self.log = W.QPlainTextEdit()
        self.log.setReadOnly(True)
        self.log.setMaximumBlockCount(2000)
        self.log_dock = W.QDockWidget('Log & Medições', self)
        self.log_dock.setWidget(self.log)
        self.log_dock.setMaximumHeight(160)
        self.addDockWidget(QtCore.Qt.BottomDockWidgetArea, self.log_dock)

        # FPS & Performance Timer (Updates every 1000ms)
        self.perf_timer = QtCore.QTimer(self)
        self.perf_timer.timeout.connect(self.update_performance_status)
        self.perf_timer.start(1000)

        # Initial Status Bar Message
        self.statusBar().showMessage(
            'Pronto | Olhar: Botão esquerdo • Pan: Botão meio • Orbit: Shift + Botão meio • Zoom: Scroll • F5: Atualizar'
        )
        self.log.appendPlainText('PlantView Studio 2026 v0.0.2 iniciado com renderização OpenGL acelerada por GPU.')

    def on_camera_changed(self, camera):
        """Update floating coordinate badges whenever camera moves."""
        eye = camera.GetPosition()
        focal = camera.GetFocalPoint()
        self.coord_overlay.update_coordinates(eye, focal)
        self.fps_counter += 1

    def update_performance_status(self):
        """Update real-time FPS and GPU statistics in the status bar."""
        now = time.time()
        dt = max(now - self.fps_last_time, 0.001)
        self.current_fps = self.fps_counter / dt
        self.fps_counter = 0
        self.fps_last_time = now

        mem = get_system_memory_info()
        actors_count = self.plot.renderer.GetActors().GetNumberOfItems() if self.plot.renderer else 0

        msg = (
            f'FPS: {self.current_fps:.1f} | '
            f'Triângulos: {self.total_triangles:,} | '
            f'Atores GPU: {actors_count} | '
            f'RAM: {mem["used_ram_mb"]:.0f} MB / {mem["total_ram_mb"]:.0f} MB ({mem["load_pct"]}%) | '
            f'Modelos: {len(self.models)} federados'
        )
        self.statusBar().showMessage(msg)

    def add_files(self):
        paths, _ = W.QFileDialog.getOpenFileNames(
            self,
            'Adicionar modelos na posição original (DWG, STEP, IFC, DXF)',
            '',
            'Modelos CAD (*.dwg *.step *.stp *.ifc *.dxf *.stl *.obj *.ply);;Todos (*)'
        )
        if paths:
            records = [
                {
                    'path': p,
                    'visible': True,
                    'scale': self.units.currentData(),
                    'mtime': os.path.getmtime(p) if os.path.exists(p) else 0
                }
                for p in paths
            ]
            self.enqueue(records)

    def enqueue(self, records):
        self.queue.extend(records)
        if self.worker is None:
            self.next_import()

    def next_import(self):
        if not self.queue:
            if self.loading_dialog:
                self.loading_dialog.accept()
                self.loading_dialog = None
            if self.restore_camera:
                self.plot.camera_position = self.restore_camera
                self.restore_camera = None
            self.statusBar().showMessage(f'{len(self.models)} modelo(s) federado(s) | Coordenadas globais reais')
            return

        record = self.queue.pop(0)
        file_name = Path(record['path']).name

        # Launch Navisworks-style Loading Dialog
        if not self.loading_dialog:
            self.loading_dialog = NavisLoadingDialog(self, title='Loading ...')
            self.loading_dialog.cancelled.connect(self.cancel_import)
            self.loading_dialog.show()

        self.loading_dialog.set_file_name(file_name)
        self.loading_dialog.set_progress(5.0, f'Lendo {file_name}...')
        self.log.appendPlainText(f'\nImportando: {record["path"]}')

        self.worker = ImportWorker(record)
        self.worker.progress.connect(self.on_import_progress)
        self.worker.loaded.connect(self.add_result)
        self.worker.failed.connect(self.on_import_failed)
        self.worker.finished.connect(self.import_finished)
        self.worker.start()

    def on_import_progress(self, pct: float, msg: str):
        if self.loading_dialog:
            self.loading_dialog.set_progress(pct, msg)

    def cancel_import(self):
        if self.worker:
            self.worker.cancel()
            self.log.appendPlainText('Importação cancelada pelo usuário.')
            self.queue.clear()

    def on_import_failed(self, error_msg: str):
        self.log.appendPlainText(f'AVISO: Falha ao carregar/atualizar arquivo: {error_msg}. A geometria anterior foi mantida.')
        self.statusBar().showMessage('Erro de leitura no arquivo; modelo anterior conservado intacto.')

    def import_finished(self):
        old = self.worker
        self.worker = None
        if old:
            old.deleteLater()
        self.next_import()

    def add_result(self, record, parts, warnings):
        previous = record.pop('_replace', None)
        index = self.models.index(previous) if previous is not None else len(self.models)

        record = dict(record, actors=[])
        record['mtime'] = os.path.getmtime(record['path']) if os.path.exists(record['path']) else 0

        # Tree Node
        root = W.QTreeWidgetItem([Path(record['path']).name])
        root.setToolTip(0, record['path'])
        root.setFlags(root.flags() | QtCore.Qt.ItemIsUserCheckable)
        self.tree.blockSignals(True)
        root.setCheckState(0, QtCore.Qt.Checked if record['visible'] else QtCore.Qt.Unchecked)

        # Register layers in LayerManager
        for name, mesh in parts:
            layer_data = mesh.field_data.get('plantview_layer')
            layer = str(layer_data[0]) if layer_data is not None else '0'
            color_data = mesh.field_data.get('plantview_rgb')
            rgb = tuple(int(x) for x in color_data[0]) if color_data is not None else None
            self.layer_manager.register(layer, rgb)

        # GPU Instancing and buffer sharing
        actors, names, stats = add_optimized_parts(self.plot, parts, visible=record['visible'])
        record['actors'].extend(actors)
        self.total_triangles += stats.get('total_triangles', sum(getattr(m, 'n_cells', 1) for _, m in parts))

        # Populate hierarchy tree
        for actor, name in zip(actors, names):
            child = W.QTreeWidgetItem([name])
            child.setData(0, QtCore.Qt.UserRole, actor)
            root.addChild(child)

        self.log.appendPlainText(
            f"GPU: {stats['original_parts']} peças processadas -> {stats['gpu_actors']} atores GPU, "
            f"{stats['instanced_parts']} instâncias em {stats['instance_groups']} grupos VRAM compartilhados."
        )

        record['item'] = root
        if previous is not None:
            # Replace previous without flickering
            for actor in previous['actors']:
                self.plot.remove_actor(actor)
            self.tree.takeTopLevelItem(index)
            self.models[index] = record
            self.tree.insertTopLevelItem(index, root)
        else:
            self.models.append(record)
            self.tree.addTopLevelItem(root)

        self.tree.blockSignals(False)
        self.plot.remove_actor('welcome')

        if previous is None and len(self.models) == 1:
            self.plot.reset_camera()

        self.dirty = True
        self.log.appendPlainText(f'Carregado: {len(parts)} peça(s) com cores preservadas.')
        for w in warnings[:50]:
            self.log.appendPlainText('AVISO: ' + w)

        self.plot.render()

    def refresh_models(self):
        """F5: Smart refresh. Checks mtime, reloads modified models, preserves camera."""
        if not self.models:
            return
        self.restore_camera = [list(v) for v in self.plot.camera_position]
        self.measure_points = []
        self.plot.remove_actor('measure')

        # Check for files modified on disk
        to_reload = []
        for m in self.models:
            path = m['path']
            current_mtime = os.path.getmtime(path) if os.path.exists(path) else 0
            # Always reload or reload modified
            to_reload.append(dict(
                path=m['path'],
                visible=m['visible'],
                scale=m.get('scale', 0.001),
                _replace=m
            ))

        self.log.appendPlainText('\n[F5 REFRESH] Verificando e recarregando modelos da maquete...')
        self.enqueue(to_reload)

    def selection_changed(self):
        """Highlights the selected actor in the 3D scene."""
        selected_items = self.tree.selectedItems()
        if not selected_items:
            if self.selected_actor:
                self.selected_actor.GetProperty().SetEdgeVisibility(False)
                self.selected_actor = None
                self.plot.render()
            return

        item = selected_items[0]
        actor = item.data(0, QtCore.Qt.UserRole)
        if actor and isinstance(actor, vtk.vtkActor):
            if self.selected_actor and self.selected_actor != actor:
                self.selected_actor.GetProperty().SetEdgeVisibility(False)
            self.selected_actor = actor
            actor.GetProperty().SetEdgeVisibility(True)
            actor.GetProperty().SetEdgeColor(1.0, 0.84, 0.0)  # Navisworks Gold highlight
            actor.GetProperty().SetLineWidth(2.5)
            self.plot.render()

    def visibility_changed(self, item, column):
        """Toggles model or group visibility from the selection tree."""
        # Check if top-level model
        for model in self.models:
            if model['item'] is item:
                model['visible'] = (item.checkState(0) == QtCore.Qt.Checked)
                for actor in model['actors']:
                    actor.SetVisibility(model['visible'])
                self.dirty = True
                self.plot.render()
                return

    def isolate(self):
        """Isolate: Hides everything except selected item."""
        selected_items = self.tree.selectedItems()
        if not selected_items:
            return
        target = selected_items[0]
        # Check if top level
        for m in self.models:
            is_match = (m['item'] is target)
            m['item'].setCheckState(0, QtCore.Qt.Checked if is_match else QtCore.Qt.Unchecked)

    def hide_selected(self):
        """Hide: Hides the currently selected model or component."""
        selected_items = self.tree.selectedItems()
        if not selected_items:
            return
        target = selected_items[0]
        for m in self.models:
            if m['item'] is target:
                m['item'].setCheckState(0, QtCore.Qt.Unchecked)
                return

    def show_all(self):
        """Unhide All: Shows all models and components."""
        for m in self.models:
            m['item'].setCheckState(0, QtCore.Qt.Checked)

    def select_same_layer(self):
        """Selects all items belonging to the same layer as the active item."""
        if not self.selected_actor or not hasattr(self.selected_actor, '_plantview_layer'):
            return
        target_layer = self.selected_actor._plantview_layer
        count = 0
        for m in self.models:
            for act in m['actors']:
                if hasattr(act, '_plantview_layer') and act._plantview_layer == target_layer:
                    act.GetProperty().SetEdgeVisibility(True)
                    act.GetProperty().SetEdgeColor(1.0, 0.84, 0.0)
                    count += 1
        self.plot.render()
        self.log.appendPlainText(f'Selecionados {count} itens da camada "{target_layer}".')

    def show_properties(self):
        """Displays properties sheet for selected item."""
        if not self.selected_actor:
            W.QMessageBox.information(self, 'Propriedades', 'Nenhum elemento selecionado na árvore ou viewport.')
            return
        name = getattr(self.selected_actor, '_plantview_name', 'Desconhecido')
        layer = getattr(self.selected_actor, '_plantview_layer', '0')
        bounds = getattr(self.selected_actor, '_plantview_bounds', None)
        pos = self.selected_actor.GetPosition()
        
        info = [
            f'Nome do Elemento: {name}',
            f'Camada (Layer): {layer}',
            f'Posição X, Y, Z: {pos[0]:.4f} m, {pos[1]:.4f} m, {pos[2]:.4f} m',
        ]
        if bounds:
            dx = bounds[1] - bounds[0]
            dy = bounds[3] - bounds[2]
            dz = bounds[5] - bounds[4]
            info.append(f'Dimensões: Largura={dx:.4f} m, Comprimento={dy:.4f} m, Altura={dz:.4f} m')
        W.QMessageBox.information(self, 'Propriedades do Elemento', '\n'.join(info))

    def show_layer_manager(self):
        """Opens the Appearance Profiler & Layer Manager dialog."""
        dlg = NavisLayerManagerDialog(self.layer_manager, self)
        dlg.color_changed.connect(self.on_layer_color_changed)
        dlg.visibility_changed.connect(self.on_layer_visibility_changed)
        dlg.exec()

    def on_layer_color_changed(self, layer_name: str, rgb: tuple):
        """Applies real-time color update to all actors in the modified layer."""
        float_color = (rgb[0] / 255.0, rgb[1] / 255.0, rgb[2] / 255.0)
        for m in self.models:
            for act in m['actors']:
                if getattr(act, '_plantview_layer', '') == layer_name:
                    act.GetProperty().SetColor(*float_color)
        self.plot.render()
        self.dirty = True

    def on_layer_visibility_changed(self, layer_name: str, visible: bool):
        """Applies visibility toggle to all actors in the layer."""
        for m in self.models:
            for act in m['actors']:
                if getattr(act, '_plantview_layer', '') == layer_name:
                    act.SetVisibility(visible and m['visible'])
        self.plot.render()

    def toggle_selection_tree(self):
        self.tree_dock.setVisible(not self.tree_dock.isVisible())

    def toggle_measure(self):
        self.measure_mode = not self.measure_mode
        self.measure_points = []
        if self.measure_mode:
            self.statusBar().showMessage('MODO MEDIR ATIVO: Clique com botão direito ou pressione P em dois pontos da maquete.')
            self.log.appendPlainText('MEDIR: Clique ou pressione P sobre duas superfícies para calcular a distância exata em metros.')
        else:
            self.statusBar().showMessage('Medição desativada.')

    def clear_measures(self):
        self.plot.remove_actor('measure')
        self.measure_points.clear()
        self.plot.render()

    def point_picked(self, point):
        if not self.measure_mode:
            return
        self.measure_points.append(np.array(point))
        if len(self.measure_points) == 2:
            a, b = self.measure_points
            dist = np.linalg.norm(a - b)
            self.plot.add_mesh(pv.Line(a, b), color='#ffcc00', line_width=4, name='measure', pickable=False, reset_camera=False)
            self.log.appendPlainText(f'MEDIDA: Distância = {dist:.4f} m ({dist * 1000:.1f} mm) | A={a.round(4)} | B={b.round(4)}')
            self.measure_points = []

    def set_perspective(self):
        camera, _ = self.navigation.camera()
        if camera:
            camera.ParallelProjectionOff()
            self.plot.render()

    def set_orthogonal(self):
        camera, _ = self.navigation.camera()
        if camera:
            camera.ParallelProjectionOn()
            self.plot.render()

    def show_gpu_info(self):
        self.plot.render()
        info = gpu_report(self.plot)
        self.log.appendPlainText('\n' + info)
        W.QMessageBox.information(self, 'PlantView Studio — Diagnóstico GPU', info)

    def save(self):
        path, _ = W.QFileDialog.getSaveFileName(self, 'Salvar projeto federado', self.project_path or 'Maquete.pvproj', 'Projeto PlantView (*.pvproj)')
        if not path:
            return False
        if not path.lower().endswith('.pvproj'):
            path += '.pvproj'
        try:
            save_project(path, self.models, [list(v) for v in self.plot.camera_position])
            self.project_path = path
            self.dirty = False
            self.log.appendPlainText(f'Projeto federado salvo com sucesso em: {path}')
            return True
        except Exception as e:
            W.QMessageBox.warning(self, 'Falha ao salvar projeto', str(e))
            return False

    def open_project(self):
        path, _ = W.QFileDialog.getOpenFileName(self, 'Abrir projeto federado', '', 'Projeto PlantView (*.pvproj)')
        if not path:
            return
        try:
            data = load_project(path)
        except Exception as e:
            W.QMessageBox.warning(self, 'Projeto inválido', str(e))
            return
        if not self.confirm_discard():
            return
        self.clear_models()
        self.project_path = path
        self.restore_camera = data.get('camera')
        self.enqueue(data['models'])

    def confirm_discard(self):
        if not self.dirty:
            return True
        ans = W.QMessageBox.question(self, 'Projeto modificado', 'Salvar o projeto antes de continuar?', W.QMessageBox.Save | W.QMessageBox.Discard | W.QMessageBox.Cancel)
        if ans == W.QMessageBox.Save:
            return self.save()
        return ans == W.QMessageBox.Discard

    def clear_models(self):
        for m in self.models:
            for actor in m['actors']:
                self.plot.remove_actor(actor)
        self.plot.remove_actor('measure')
        self.models.clear()
        self.tree.clear()
        self.total_triangles = 0
        self.project_path = None
        self.dirty = False

    def new_project(self):
        if self.confirm_discard():
            self.clear_models()

    def closeEvent(self, event):
        if self.worker:
            W.QMessageBox.information(self, 'Importação em andamento', 'Aguarde o término da importação para fechar.')
            event.ignore()
            return
        if not self.confirm_discard():
            event.ignore()
            return
        self.plot.close()
        event.accept()


def main():
    configure_surface()
    app = W.QApplication(sys.argv)
    app.setApplicationName('PlantView Studio')
    app.setWindowIcon(create_navis_icon('app_logo', 64))

    window = Window()
    window.show()

    if '--smoke-test' in sys.argv:
        import json
        output = Path(sys.argv[sys.argv.index('--smoke-test') + 1]).resolve()
        output.mkdir(parents=True, exist_ok=True)
        root = Path(sys.executable).parent if getattr(sys, 'frozen', False) else Path(__file__).resolve().parents[1]
        report = {'models': [], 'errors': []}

        def check():
            for name in ('equipamentos.dwg', 'estrutura.step', 'parede.ifc'):
                try:
                    path = root / 'examples' / name
                    if path.is_file():
                        parts, warnings = read_model(path)
                        window.add_result({'path': str(path), 'visible': True, 'scale': 0.001}, parts, warnings)
                        report['models'].append({
                            'file': name,
                            'parts': len(parts),
                            'bounds': [list(m.bounds) for _, m in parts],
                            'warnings': warnings
                        })
                except Exception as e:
                    report['errors'].append(f'{name}: {e}')
            window.plot.view_isometric()
            window.plot.reset_camera()
            QtCore.QTimer.singleShot(1500, finish)

        def finish():
            window.grab().save(str(output / 'PlantViewStudio.png'))
            window.plot.screenshot(str(output / 'viewport.png'))
            (output / 'smoke-test.json').write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8')
            window.dirty = False
            window.close()
            app.exit(1 if report['errors'] else 0)

        QtCore.QTimer.singleShot(600, check)

    return app.exec()
