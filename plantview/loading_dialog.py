"""Autodesk Navisworks-style Loading Progress Dialog.

Reproduces the exact UI layout from Navisworks Manage:
- Dialog Title: "Loading ..."
- Percentage readout: "0,00%"
- Primary progress bar
- Filename and current phase: "Loading ESTUDO - NOME.dwg ..."
- Secondary sub-progress bar
- Bottom right "Cancel" button
"""
from PySide6 import QtCore, QtGui, QtWidgets as W


class NavisLoadingDialog(W.QDialog):
    cancelled = QtCore.Signal()

    def __init__(self, parent=None, title='PlantView • Abrindo modelo'):
        super().__init__(parent, QtCore.Qt.Window | QtCore.Qt.WindowTitleHint | QtCore.Qt.WindowCloseButtonHint)
        self.setWindowTitle(title)
        self.setMinimumSize(560, 200)
        self.setStyleSheet("""
            QDialog {
                background-color: #f5f7fb;
                color: #1e1e1e;
                font-family: 'Segoe UI', Tahoma, sans-serif;
            }
            QLabel {
                color: #202020;
                font-size: 12px;
            }
            QLabel#pctLabel {
                font-size: 13px;
                font-weight: 600;
                color: #1a1a1a;
            }
            QLabel#fileLabel {
                font-size: 12px;
                color: #2b2b2b;
            }
            QProgressBar {
                border: none;
                border-radius: 6px;
                background-color: #e6e6e6;
                height: 16px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #1677d2;
                border-radius: 6px;
            }
            QPushButton {
                background-color: #e1e1e1;
                border: 1px solid #adadad;
                padding: 5px 20px;
                font-size: 12px;
                min-width: 75px;
            }
            QPushButton:hover {
                background-color: #e5f1fb;
                border: 1px solid #0078d4;
            }
            QPushButton:pressed {
                background-color: #cce4f7;
            }
        """)

        layout = W.QVBoxLayout(self)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(6)

        # Percentage label at top
        self.pct_label = W.QLabel('0,00%')
        self.pct_label.setObjectName('pctLabel')
        self.pct_label.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(self.pct_label)

        # Primary Progress Bar
        self.bar_main = W.QProgressBar()
        self.bar_main.setRange(0, 10000)
        self.bar_main.setValue(0)
        self.bar_main.setTextVisible(False)
        layout.addWidget(self.bar_main)

        # File & action label
        self.file_label = W.QLabel('Preparando modelo...')
        self.file_label.setObjectName('fileLabel')
        layout.addWidget(self.file_label)

        # Sub Progress Bar
        self.bar_sub = W.QProgressBar()
        self.bar_sub.setRange(0, 100)
        self.bar_sub.setValue(0)
        self.bar_sub.setTextVisible(False)
        layout.addWidget(self.bar_sub)

        # Bottom row with Cancel button on right
        btn_layout = W.QHBoxLayout()
        btn_layout.addStretch()
        self.cancel_btn = W.QPushButton('Cancelar')
        self.cancel_btn.clicked.connect(self.on_cancel)
        btn_layout.addWidget(self.cancel_btn)
        layout.addLayout(btn_layout)

        self._is_cancelled = False

    def set_progress(self, pct: float, message: str = ''):
        """Update percentage (0.0 to 100.0) and message."""
        self.bar_main.setValue(int(pct * 100))
        self.pct_label.setText(f'{pct:.2f}%'.replace('.', ','))
        if message:
            self.file_label.setText(message)
            # Alternate sub bar to give feedback
            self.bar_sub.setRange(0, 0) if 10 <= pct < 60 else self.bar_sub.setRange(0, 100)
            if pct >= 60:
                self.bar_sub.setValue(int(pct))
        QtCore.QCoreApplication.processEvents()

    def set_file_name(self, filename: str):
        self.file_label.setText(f'Loading {filename} ...')
        QtCore.QCoreApplication.processEvents()

    def on_cancel(self):
        self._is_cancelled = True
        self.cancelled.emit()
        self.reject()

    def is_cancelled(self) -> bool:
        return self._is_cancelled

