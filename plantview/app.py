import os
os.environ['QT_API'] = 'pyside6'
import sys
from pathlib import Path
import numpy as np
from PySide6 import QtCore, QtGui, QtWidgets as W
from pyvistaqt import QtInteractor
import pyvista as pv
from .readers import read_model
from .project import load_project, save_project

class ImportWorker(QtCore.QThread):
    loaded = QtCore.Signal(object, object, object)
    failed = QtCore.Signal(str)
    def __init__(self, record):
        super().__init__()
        self.record = record
    def run(self):
        try:
            parts, warnings = read_model(self.record['path'], unit_scale=self.record['scale'])
            self.loaded.emit(self.record, parts, warnings)
        except Exception as e: self.failed.emit(str(e))

class Window(W.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('PlantView Studio | Maquete federada — 0.1 experimental')
        self.resize(1320, 850)
        self.models = []
        self.queue = []
        self.worker = None
        self.dirty = False
        self.project_path = None
        self.restore_camera = None
        self.measure_points = []
        self.measure_mode = False
        self.actions = []
        self.setStyleSheet('QMainWindow,QWidget{background:#172433;color:#e4edf6;} QToolBar{background:#22364b;padding:8px;spacing:7px;} QToolButton{padding:7px;} QTreeWidget,QPlainTextEdit{background:#102030;border:1px solid #30465b;} QHeaderView::section{background:#22364b;padding:7px;} QPushButton{padding:7px;background:#284763;} QComboBox{padding:5px;background:#284763;}')
        central = W.QWidget()
        layout = W.QVBoxLayout(central)
        layout.setContentsMargins(0,0,0,0)
        banner = W.QLabel('  PLANTVIEW STUDIO    /    Coordenação 3D local    •    Coordenadas em metros')
        banner.setMinimumHeight(42)
        banner.setStyleSheet('background:#22364b;color:#71d4d1;font-size:15px;font-weight:600;')
        layout.addWidget(banner)
        self.plot = QtInteractor(central)
        layout.addWidget(self.plot.interactor)
        self.setCentralWidget(central)
        self.plot.set_background('#101d2a', top='#294256')
        self.plot.add_axes()
        self.plot.enable_trackball_style()
        self.plot.enable_surface_point_picking(callback=self.point_picked, show_message=False,
                                              show_point=False, left_clicking=False)
        self.plot.add_text('Adicione modelos para montar sua maquete\nDWG • STEP • IFC • DXF', name='welcome', font_size=14, color='#b8ccdb')
        self.tree = W.QTreeWidget()
        self.tree.setHeaderLabels(['Modelos e elementos'])
        self.tree.itemChanged.connect(self.visibility_changed)
        self.tree.itemSelectionChanged.connect(self.selection_changed)
        dock = W.QDockWidget('Modelos', self)
        dock.setWidget(self.tree)
        dock.setMinimumWidth(290)
        self.addDockWidget(QtCore.Qt.LeftDockWidgetArea, dock)
        self.log = W.QPlainTextEdit()
        self.log.setReadOnly(True)
        self.log.setMaximumBlockCount(2000)
        logdock = W.QDockWidget('Relatório de importação e medidas', self)
        logdock.setWidget(self.log)
        self.addDockWidget(QtCore.Qt.BottomDockWidgetArea, logdock)
        logdock.setMaximumHeight(190)
        toolbar = self.addToolBar('Projeto')
        toolbar.setMovable(False)
        def action(label, callback, shortcut=None):
            a = QtGui.QAction(label, self)
            a.triggered.connect(callback)
            if shortcut: a.setShortcut(shortcut)
            toolbar.addAction(a)
            self.actions.append(a)
            return a
        action('+ Adicionar modelos', self.add_files, 'Ctrl+I')
        action('Abrir projeto', self.open_project, 'Ctrl+O')
        action('Salvar', self.save, 'Ctrl+S')
        action('Novo', self.new_project, 'Ctrl+N')
        action('Atualizar modelos', self.refresh_models, 'F5')
        toolbar.addSeparator()
        action('Enquadrar', self.plot.reset_camera, 'F')
        action('Isolar', self.isolate)
        action('Mostrar todos', self.show_all)
        action('Remover', self.remove_selected)
        action('Medir', self.toggle_measure)
        action('Ajuda', self.help)
        self.units = W.QComboBox()
        for label, scale in [('mm', .001), ('m', 1.), ('cm', .01), ('pol', .0254)]: self.units.addItem(label, scale)
        self.units.setToolTip('Unidade para malhas e DWG/DXF sem unidade reconhecida. Defina antes de adicionar.')
        toolbar.addWidget(W.QLabel('  Unidade de origem:'))
        toolbar.addWidget(self.units)
        self.statusBar().showMessage('Pronto | Arraste: orbitar • Shift + arrastar: mover • Roda: zoom • Medir: tecla P sobre a superfície')
        self.log.appendPlainText('Versão experimental. DWG usa motor livre incorporado; verifique o relatório e as coordenadas antes de utilizar resultados.')

    def add_files(self):
        paths, _ = W.QFileDialog.getOpenFileNames(self, 'Adicionar modelos na posição original', '', 'Modelos (*.dwg *.step *.stp *.ifc *.dxf *.stl *.obj *.ply *.vtp);;Todos (*)')
        self.enqueue([{'path': p, 'visible': True, 'scale': self.units.currentData()} for p in paths])

    def enqueue(self, records):
        self.queue.extend(records)
        if self.worker is None: self.next_import()

    def next_import(self):
        if not self.queue:
            self.worker = None
            for a in self.actions: a.setEnabled(True)
            if self.restore_camera:
                self.plot.camera_position = self.restore_camera
                self.restore_camera = None
            self.statusBar().showMessage(f'{len(self.models)} modelo(s) | Coordenadas globais em metros')
            return
        record = self.queue.pop(0)
        for a in self.actions: a.setEnabled(False)
        self.statusBar().showMessage('Lendo ' + Path(record['path']).name + '…')
        self.log.appendPlainText('\nLendo: ' + record['path'])
        self.worker = ImportWorker(record)
        self.worker.loaded.connect(self.add_result)
        self.worker.failed.connect(lambda e: self.log.appendPlainText('ERRO: ' + e))
        self.worker.finished.connect(self.import_finished)
        self.worker.start()

    def import_finished(self):
        old = self.worker
        self.worker = None
        old.deleteLater()
        self.next_import()

    def add_result(self, record, parts, warnings):
        colors = ['#55c7c3', '#e3b86c', '#83a9ef', '#d38ba9', '#9bc789']
        previous = record.pop('_replace', None)
        index = self.models.index(previous) if previous is not None else len(self.models)
        color = colors[index % len(colors)]
        record = dict(record, actors=[])
        root = W.QTreeWidgetItem([Path(record['path']).name])
        root.setToolTip(0, record['path'])
        root.setFlags(root.flags() | QtCore.Qt.ItemIsUserCheckable)
        self.tree.blockSignals(True)
        root.setCheckState(0, QtCore.Qt.Checked if record['visible'] else QtCore.Qt.Unchecked)
        for name, mesh in parts:
            actor = self.plot.add_mesh(mesh, color=color, smooth_shading=False, reset_camera=False, line_width=2)
            actor.SetVisibility(record['visible'])
            record['actors'].append(actor)
            child = W.QTreeWidgetItem([name])
            root.addChild(child)
        record['item'] = root
        if previous is not None:
            for actor in previous['actors']: self.plot.remove_actor(actor)
            self.tree.takeTopLevelItem(index)
            self.models[index] = record
            self.tree.insertTopLevelItem(index, root)
        else:
            self.models.append(record)
            self.tree.addTopLevelItem(root)
        self.tree.blockSignals(False)
        self.plot.remove_actor('welcome')
        if previous is None: self.plot.reset_camera()
        self.dirty = True
        self.log.appendPlainText(f'Carregado: {len(parts)} elemento(s).')
        for warning in warnings[:100]: self.log.appendPlainText('AVISO: ' + warning)
        if len(warnings) > 100: self.log.appendPlainText(f'Outros {len(warnings)-100} avisos omitidos.')

    def refresh_models(self):
        if not self.models: return
        self.restore_camera = [list(v) for v in self.plot.camera_position]
        self.measure_points = []
        self.plot.remove_actor('measure')
        self.log.appendPlainText('ATUALIZAR: relendo os arquivos originais. Em caso de erro, a geometria anterior será mantida.')
        records = [dict(path=m['path'], visible=m['visible'], scale=m['scale'], _replace=m) for m in self.models]
        self.enqueue(records)

    def selected_model(self):
        item = self.tree.currentItem()
        if item is None: return None
        while item.parent(): item = item.parent()
        return next((m for m in self.models if m['item'] is item), None)

    def selection_changed(self):
        model = self.selected_model()
        for m in self.models:
            for actor in m['actors']:
                actor.GetProperty().SetEdgeVisibility(m is model)
        self.plot.render()

    def visibility_changed(self, item, column):
        for model in self.models:
            if model['item'] is item:
                model['visible'] = item.checkState(0) == QtCore.Qt.Checked
                for actor in model['actors']: actor.SetVisibility(model['visible'])
                self.dirty = True
        self.plot.render()

    def isolate(self):
        selected = self.selected_model()
        if selected:
            for m in self.models: m['item'].setCheckState(0, QtCore.Qt.Checked if m is selected else QtCore.Qt.Unchecked)

    def show_all(self):
        for m in self.models: m['item'].setCheckState(0, QtCore.Qt.Checked)

    def remove_selected(self):
        m = self.selected_model()
        if m:
            for a in m['actors']: self.plot.remove_actor(a)
            self.tree.takeTopLevelItem(self.tree.indexOfTopLevelItem(m['item']))
            self.models.remove(m)
            self.dirty = True

    def toggle_measure(self):
        self.measure_mode = not self.measure_mode
        self.measure_points = []
        self.log.appendPlainText('MEDIR: posicione o cursor e pressione P em duas superfícies. Distância aproximada da malha, em metros.' if self.measure_mode else 'Medição desativada.')

    def point_picked(self, point):
        if not self.measure_mode: return
        self.measure_points.append(np.array(point))
        if len(self.measure_points) == 2:
            a,b = self.measure_points
            distance = np.linalg.norm(a-b)
            self.plot.add_mesh(pv.Line(a,b), color='yellow', line_width=4, name='measure', pickable=False, reset_camera=False)
            self.log.appendPlainText(f'Distância aproximada: {distance:.6f} m | A={a.round(6)} | B={b.round(6)}')
            self.measure_points = []

    def save(self):
        path, _ = W.QFileDialog.getSaveFileName(self, 'Salvar projeto', self.project_path or 'Maquete.pvproj', 'Projeto PlantView (*.pvproj)')
        if not path: return False
        if not path.lower().endswith('.pvproj'): path += '.pvproj'
        try:
            save_project(path, self.models, [list(v) for v in self.plot.camera_position])
            self.project_path = path
            self.dirty = False
            self.log.appendPlainText('Projeto salvo. Ele referencia os arquivos originais; mantenha-os disponíveis.')
            return True
        except Exception as e:
            W.QMessageBox.warning(self, 'Falha ao salvar', str(e)); return False

    def confirm_discard(self):
        if not self.dirty: return True
        answer = W.QMessageBox.question(self, 'Projeto modificado', 'Salvar o projeto antes de continuar?', W.QMessageBox.Save | W.QMessageBox.Discard | W.QMessageBox.Cancel)
        if answer == W.QMessageBox.Save: return self.save()
        return answer == W.QMessageBox.Discard

    def clear_models(self):
        for m in self.models:
            for actor in m['actors']: self.plot.remove_actor(actor)
        self.plot.remove_actor('measure')
        self.models.clear()
        self.tree.clear()
        self.project_path = None
        self.dirty = False

    def new_project(self):
        if self.confirm_discard(): self.clear_models()

    def open_project(self):
        path, _ = W.QFileDialog.getOpenFileName(self, 'Abrir projeto', '', 'Projeto PlantView (*.pvproj)')
        if not path: return
        try: data = load_project(path)
        except Exception as e:
            W.QMessageBox.warning(self, 'Projeto inválido', str(e)); return
        if not self.confirm_discard(): return
        self.clear_models()
        self.project_path = path
        self.restore_camera = data.get('camera')
        self.enqueue(data['models'])

    def help(self):
        W.QMessageBox.information(self, 'PlantView Studio — Ajuda',
            'Adicione vários arquivos; as coordenadas originais são preservadas e convertidas para metros.\n\n'
            'Mouse: arrastar para orbitar, Shift + arrastar para mover, roda para zoom, F para enquadrar.\n'
            'Árvore: marque/desmarque para visibilidade. Selecione um modelo para isolar/remover.\n'
            'Medir: ative e pressione P sobre duas superfícies. Medição aproximada da malha.\n\n'
            'Atualizar modelos (F5): releia todos os arquivos após salvá-los no programa de origem. Câmera e visibilidade são mantidas; falhas conservam a geometria anterior.\n\n'
            'DWG: leitor livre experimental incorporado, sem AutoCAD. Compatibilidade não equivale ao Navisworks.\n'
            'NWC/NWD/RVT não são suportados. Sem detecção de interferências, 4D ou edição CAD.\n'
            'Projetos referenciam os arquivos originais; não incorporam os modelos.')

    def closeEvent(self, event):
        if self.worker:
            W.QMessageBox.information(self, 'Importação em andamento', 'Aguarde o término da importação para fechar.'); event.ignore(); return
        if not self.confirm_discard(): event.ignore(); return
        self.plot.close()
        event.accept()

def main():
    app = W.QApplication(sys.argv)
    app.setApplicationName('PlantView Studio')
    window = Window()
    window.show()
    if '--smoke-test' in sys.argv:
        import json
        output = Path(sys.argv[sys.argv.index('--smoke-test')+1]).resolve()
        output.mkdir(parents=True, exist_ok=True)
        root = Path(sys.executable).parent if getattr(sys, 'frozen', False) else Path(__file__).resolve().parents[1]
        report = {'models': [], 'errors': []}
        def check():
            for name in ('equipamentos.dwg', 'estrutura.step', 'parede.ifc'):
                try:
                    path = root / 'examples' / name
                    parts, warnings = read_model(path)
                    window.add_result({'path':str(path),'visible':True,'scale':.001},parts,warnings)
                    report['models'].append({'file':name,'parts':len(parts),'bounds':[list(m.bounds) for _,m in parts],'warnings':warnings})
                except Exception as e: report['errors'].append(f'{name}: {e}')
            window.plot.view_isometric()
            window.plot.reset_camera()
            QtCore.QTimer.singleShot(1200, finish)
        def finish():
            window.grab().save(str(output/'PlantViewStudio.png'))
            window.plot.screenshot(str(output/'viewport.png'))
            (output/'smoke-test.json').write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')
            window.dirty = False
            window.close()
            app.exit(1 if report['errors'] else 0)
        QtCore.QTimer.singleShot(500, check)
    return app.exec()
