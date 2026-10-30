"""Autodesk Navisworks Manage Ribbon UI Bar.

Implements the ribbon styling and button groups seen in Navisworks Manage:
- Quick Access Toolbar (New, Open, Save, Refresh F5)
- Tab Strip: Home, Viewpoint, Review, Display
- Group Containers: Project, Select & Search, Visibility, Display, Tools
"""
from PySide6 import QtCore, QtGui, QtWidgets as W
from .icons import create_navis_icon


class NavisRibbonGroup(W.QFrame):
    """A vertical ribbon group panel with title label at the bottom."""
    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.setObjectName('ribbonGroup')
        self.setStyleSheet("""
            QFrame#ribbonGroup {
                background-color: #fafafa;
                border: 1px solid #dcdcdc;
                border-radius: 3px;
                margin: 2px;
            }
            QLabel#groupTitle {
                color: #555555;
                font-size: 10px;
                font-weight: 500;
                padding-bottom: 2px;
            }
            QToolButton {
                background-color: transparent;
                border: 1px solid transparent;
                border-radius: 3px;
                padding: 4px;
                font-size: 11px;
                color: #222222;
            }
            QToolButton:hover {
                background-color: #e5f1fb;
                border: 1px solid #70c0e8;
            }
            QToolButton:pressed {
                background-color: #cce4f7;
                border: 1px solid #0078d4;
            }
        """)

        layout = W.QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 2)
        layout.setSpacing(2)

        self.content_layout = W.QHBoxLayout()
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(4)
        layout.addLayout(self.content_layout)

        title_lbl = W.QLabel(title)
        title_lbl.setObjectName('groupTitle')
        title_lbl.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(title_lbl)

    def add_large_button(self, text: str, icon_name: str, callback, tooltip: str = '', shortcut: str = None) -> W.QToolButton:
        btn = W.QToolButton()
        btn.setIcon(create_navis_icon(icon_name, 32))
        btn.setIconSize(QtCore.QSize(30, 30))
        btn.setText(text)
        btn.setToolButtonStyle(QtCore.Qt.ToolButtonTextUnderIcon)
        btn.clicked.connect(callback)
        if tooltip:
            if shortcut:
                tooltip += f' ({shortcut})'
            btn.setToolTip(tooltip)
        if shortcut:
            btn.setShortcut(QtGui.QKeySequence(shortcut))
        btn.setMinimumWidth(56)
        btn.setMinimumHeight(64)
        self.content_layout.addWidget(btn)
        return btn

    def add_small_button(self, text: str, icon_name: str, callback, tooltip: str = '', shortcut: str = None) -> W.QToolButton:
        btn = W.QToolButton()
        btn.setIcon(create_navis_icon(icon_name, 20))
        btn.setIconSize(QtCore.QSize(18, 18))
        btn.setText(text)
        btn.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)
        btn.clicked.connect(callback)
        if tooltip:
            if shortcut:
                tooltip += f' ({shortcut})'
            btn.setToolTip(tooltip)
        if shortcut:
            btn.setShortcut(QtGui.QKeySequence(shortcut))
        btn.setFixedHeight(24)
        self.content_layout.addWidget(btn)
        return btn

    def add_vertical_subgroup(self) -> W.QVBoxLayout:
        vbox = W.QVBoxLayout()
        vbox.setContentsMargins(0, 0, 0, 0)
        vbox.setSpacing(2)
        self.content_layout.addLayout(vbox)
        return vbox


class NavisRibbonBar(W.QWidget):
    """Full Autodesk Navisworks Manage styled ribbon bar with tabs."""
    def __init__(self, window):
        super().__init__(window)
        self.window = window
        self.setFixedHeight(120)
        self.setStyleSheet("""
            NavisRibbonBar {
                background-color: #f3f3f3;
                border-bottom: 1px solid #b8b8b8;
            }
            QTabWidget::pane {
                border-top: 1px solid #d4d4d4;
                background-color: #f8f8f8;
            }
            QTabBar::tab {
                background: #e1e1e1;
                border: 1px solid #cccccc;
                border-bottom: none;
                padding: 5px 16px;
                font-size: 11px;
                font-weight: 500;
                color: #333333;
                min-width: 65px;
            }
            QTabBar::tab:selected {
                background: #f8f8f8;
                border-color: #0078d4;
                border-top: 2px solid #0078d4;
                color: #004578;
                font-weight: 600;
            }
            QTabBar::tab:hover:!selected {
                background: #ebebeb;
            }
        """)

        main_layout = W.QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Tabs
        self.tabs = W.QTabWidget()
        main_layout.addWidget(self.tabs)

        self._build_home_tab()
        self._build_viewpoint_tab()
        self._build_review_tab()

    def _build_home_tab(self):
        page = W.QWidget()
        layout = W.QHBoxLayout(page)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(6)

        # 1. Project Group
        grp_proj = NavisRibbonGroup('Project', page)
        grp_proj.add_large_button('Append', 'append', self.window.add_files, 'Adicionar modelos na maquete federada', 'Ctrl+I')
        
        v_proj = grp_proj.add_vertical_subgroup()
        b_ref = W.QToolButton()
        b_ref.setIcon(create_navis_icon('refresh', 18))
        b_ref.setText('Refresh')
        b_ref.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)
        b_ref.clicked.connect(self.window.refresh_models)
        b_ref.setToolTip('Atualizar modelos modificados (F5)')
        b_ref.setShortcut(QtGui.QKeySequence('F5'))
        v_proj.addWidget(b_ref)

        b_rst = W.QToolButton()
        b_rst.setIcon(create_navis_icon('reset', 18))
        b_rst.setText('Reset All')
        b_rst.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)
        b_rst.clicked.connect(self.window.plot.reset_camera)
        b_rst.setToolTip('Enquadrar todos os modelos (F)')
        b_rst.setShortcut(QtGui.QKeySequence('F'))
        v_proj.addWidget(b_rst)

        # Units dropdown
        units_row = W.QHBoxLayout()
        units_row.addWidget(W.QLabel('Unid:'))
        self.window.units = W.QComboBox()
        for label, scale in [('mm', 0.001), ('m', 1.0), ('cm', 0.01), ('pol', 0.0254)]:
            self.window.units.addItem(label, scale)
        self.window.units.setToolTip('Unidade de escala para arquivos sem unidade')
        units_row.addWidget(self.window.units)
        v_proj.addLayout(units_row)
        layout.addWidget(grp_proj)

        # 2. Select & Search Group
        grp_sel = NavisRibbonGroup('Select & Search', page)
        grp_sel.add_large_button('Select', 'select', lambda: None, 'Modo de seleção de componentes')
        grp_sel.add_large_button('Selection\nTree', 'tree', self.window.toggle_selection_tree, 'Alternar árvore de componentes')
        v_sel = grp_sel.add_vertical_subgroup()
        b_selall = W.QToolButton()
        b_selall.setText('Select All')
        b_selall.clicked.connect(self.window.show_all)
        v_sel.addWidget(b_selall)
        b_selsame = W.QToolButton()
        b_selsame.setText('Select Same')
        b_selsame.clicked.connect(self.window.select_same_layer)
        v_sel.addWidget(b_selsame)
        layout.addWidget(grp_sel)

        # 3. Visibility Group
        grp_vis = NavisRibbonGroup('Visibility', page)
        grp_vis.add_large_button('Hide', 'hide', self.window.hide_selected, 'Ocultar itens selecionados', 'Ctrl+H')
        grp_vis.add_large_button('Hide\nUnselected', 'isolate', self.window.isolate, 'Isolar itens selecionados')
        grp_vis.add_large_button('Unhide\nAll', 'unhide', self.window.show_all, 'Mostrar todos os componentes')
        layout.addWidget(grp_vis)

        # 4. Display Group
        grp_disp = NavisRibbonGroup('Display', page)
        grp_disp.add_large_button('Properties', 'properties', self.window.show_properties, 'Propriedades do item selecionado')
        grp_disp.add_large_button('Appearance\nProfiler', 'layers', self.window.show_layer_manager, 'Gerenciador de Cores e Camadas DWG')
        layout.addWidget(grp_disp)

        # 5. Tools Group
        grp_tools = NavisRibbonGroup('Tools', page)
        grp_tools.add_large_button('Measure', 'measure', self.window.toggle_measure, 'Medição 3D ponto-a-ponto', 'M')
        grp_tools.add_large_button('GPU\nDiagnostics', 'gpu', self.window.show_gpu_info, 'Diagnóstico de hardware OpenGL e memória')
        layout.addWidget(grp_tools)

        layout.addStretch()
        self.tabs.addTab(page, 'Home')

    def _build_viewpoint_tab(self):
        page = W.QWidget()
        layout = W.QHBoxLayout(page)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(6)

        # Camera Navigate Group
        grp_nav = NavisRibbonGroup('Navigate', page)
        grp_nav.add_large_button('Look\nAround', 'look', lambda: None, 'Olhar livremente ao redor (Botão esquerdo)')
        grp_nav.add_large_button('Orbit', 'orbit', lambda: None, 'Ferramenta Orbital (Shift + Botão do meio)')
        layout.addWidget(grp_nav)

        # Camera Views Group
        grp_views = NavisRibbonGroup('Views', page)
        grp_views.add_large_button('Home\nView', 'reset', self.window.plot.view_isometric, 'Vista isométrica padrão')
        
        v_views = grp_views.add_vertical_subgroup()
        b_top = W.QToolButton()
        b_top.setText('Top (Superior)')
        b_top.clicked.connect(self.window.plot.view_xy)
        v_views.addWidget(b_top)

        b_front = W.QToolButton()
        b_front.setText('Front (Frontal)')
        b_front.clicked.connect(self.window.plot.view_xz)
        v_views.addWidget(b_front)

        b_right = W.QToolButton()
        b_right.setText('Right (Lateral)')
        b_right.clicked.connect(self.window.plot.view_yz)
        v_views.addWidget(b_right)
        layout.addWidget(grp_views)

        # Camera Projection Group
        grp_proj = NavisRibbonGroup('Camera', page)
        v_cam = grp_proj.add_vertical_subgroup()
        b_persp = W.QToolButton()
        b_persp.setText('Perspectiva')
        b_persp.clicked.connect(self.window.set_perspective)
        v_cam.addWidget(b_persp)
        b_ortho = W.QToolButton()
        b_ortho.setText('Ortogonal')
        b_ortho.clicked.connect(self.window.set_orthogonal)
        v_cam.addWidget(b_ortho)
        layout.addWidget(grp_proj)

        layout.addStretch()
        self.tabs.addTab(page, 'Viewpoint')

    def _build_review_tab(self):
        page = W.QWidget()
        layout = W.QHBoxLayout(page)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(6)

        grp_meas = NavisRibbonGroup('Measure', page)
        grp_meas.add_large_button('Point to\nPoint', 'measure', self.window.toggle_measure, 'Medir distância entre 2 superfícies')
        grp_meas.add_large_button('Clear', 'reset', self.window.clear_measures, 'Limpar medições')
        layout.addWidget(grp_meas)

        layout.addStretch()
        self.tabs.addTab(page, 'Review')

