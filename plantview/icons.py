"""Procedural high-DPI icon generator matching Autodesk Navisworks Manage styling."""
from PySide6 import QtCore, QtGui


def create_navis_icon(name: str, size: int = 32) -> QtGui.QIcon:
    pix = QtGui.QPixmap(size, size)
    pix.fill(QtCore.Qt.transparent)
    p = QtGui.QPainter(pix)
    p.setRenderHint(QtGui.QPainter.Antialiasing)

    if name == 'append':
        # Green plus sign on document (like Navisworks Append)
        p.setPen(QtGui.QPen(QtGui.QColor('#4a5568'), 1.5))
        p.setBrush(QtGui.QBrush(QtGui.QColor('#edf2f7')))
        p.drawRoundedRect(4, 4, size - 14, size - 8, 2, 2)
        # Green plus circle
        p.setPen(QtCore.Qt.NoPen)
        p.setBrush(QtGui.QBrush(QtGui.QColor('#2fb344')))
        p.drawEllipse(size - 14, size - 14, 12, 12)
        p.setPen(QtGui.QPen(QtGui.QColor('white'), 2))
        p.drawLine(size - 8, size - 12, size - 8, size - 4)
        p.drawLine(size - 12, size - 8, size - 4, size - 8)

    elif name == 'refresh':
        # Circular sync arrows (green/blue)
        p.setPen(QtGui.QPen(QtGui.QColor('#0078d4'), 2.5, QtCore.Qt.SolidLine, QtCore.Qt.RoundCap))
        p.drawArc(6, 6, size - 12, size - 12, 45 * 16, 270 * 16)
        # Arrowhead
        p.setBrush(QtGui.QBrush(QtGui.QColor('#0078d4')))
        p.setPen(QtCore.Qt.NoPen)
        pts = [QtCore.QPoint(size - 5, size // 2 - 3), QtCore.QPoint(size - 1, size // 2 + 5), QtCore.QPoint(size - 9, size // 2 + 4)]
        p.drawPolygon(pts)

    elif name == 'reset':
        # Screen fit / View frame with arrows
        p.setPen(QtGui.QPen(QtGui.QColor('#2b6cb0'), 2))
        p.setBrush(QtCore.Qt.NoBrush)
        p.drawRect(5, 5, size - 10, size - 10)
        p.drawLine(2, 2, 7, 2)
        p.drawLine(2, 2, 2, 7)
        p.drawLine(size - 3, 2, size - 8, 2)
        p.drawLine(size - 3, 2, size - 3, 7)
        p.drawLine(2, size - 3, 7, size - 3)
        p.drawLine(2, size - 3, 2, size - 8)
        p.drawLine(size - 3, size - 3, size - 8, size - 3)
        p.drawLine(size - 3, size - 3, size - 3, size - 8)

    elif name == 'select':
        # Classic cursor arrow
        p.setPen(QtGui.QPen(QtGui.QColor('#1a202c'), 1.5))
        p.setBrush(QtGui.QBrush(QtGui.QColor('#edf2f7')))
        arrow = [
            QtCore.QPoint(6, 4),
            QtCore.QPoint(6, size - 8),
            QtCore.QPoint(size // 2 - 2, size // 2 + 2),
            QtCore.QPoint(size - 8, size - 4),
            QtCore.QPoint(size - 4, size - 8),
            QtCore.QPoint(size // 2 + 2, size // 2 - 2),
            QtCore.QPoint(size - 6, size // 2 - 2),
        ]
        p.drawPolygon(arrow)

    elif name == 'tree':
        # Selection tree icon
        p.setPen(QtGui.QPen(QtGui.QColor('#2b6cb0'), 1.5))
        p.setBrush(QtGui.QBrush(QtGui.QColor('#bee3f8')))
        p.drawRect(4, 5, 8, 6)
        p.drawRect(14, 13, 8, 6)
        p.drawRect(14, 21, 8, 6)
        p.drawLine(8, 11, 8, 24)
        p.drawLine(8, 16, 14, 16)
        p.drawLine(8, 24, 14, 24)

    elif name == 'hide':
        # Green cube with ghost / eye off
        p.setPen(QtGui.QPen(QtGui.QColor('#48bb78'), 1.5))
        p.setBrush(QtGui.QBrush(QtGui.QColor('#9ae6b4')))
        p.drawRect(5, 5, size - 14, size - 14)
        # Red cross / slash
        p.setPen(QtGui.QPen(QtGui.QColor('#e53e3e'), 2.5))
        p.drawLine(3, size - 5, size - 5, 3)

    elif name == 'unhide':
        # Bright visible solid cube
        p.setPen(QtGui.QPen(QtGui.QColor('#2b6cb0'), 1.5))
        p.setBrush(QtGui.QBrush(QtGui.QColor('#63b3ed')))
        p.drawRect(6, 6, size - 12, size - 12)
        # Small sparkle/sun
        p.setPen(QtGui.QPen(QtGui.QColor('#ecc94b'), 2))
        p.drawPoint(size - 4, 4)

    elif name == 'isolate':
        # Single solid cube with dotted surroundings
        p.setPen(QtGui.QPen(QtGui.QColor('#3182ce'), 1.5))
        p.setBrush(QtGui.QBrush(QtGui.QColor('#4299e1')))
        p.drawRect(9, 9, size - 18, size - 18)
        p.setPen(QtGui.QPen(QtGui.QColor('#a0aec0'), 1.5, QtCore.Qt.DotLine))
        p.setBrush(QtCore.Qt.NoBrush)
        p.drawRect(3, 3, size - 6, size - 6)

    elif name == 'properties':
        # Property sheet dialog
        p.setPen(QtGui.QPen(QtGui.QColor('#4a5568'), 1.5))
        p.setBrush(QtGui.QBrush(QtGui.QColor('#ffffff')))
        p.drawRect(5, 4, size - 10, size - 8)
        p.setPen(QtGui.QPen(QtGui.QColor('#3182ce'), 1.5))
        p.drawLine(8, 9, size - 8, 9)
        p.setPen(QtGui.QPen(QtGui.QColor('#718096'), 1.5))
        p.drawLine(8, 14, size - 8, 14)
        p.drawLine(8, 19, size - 12, 19)

    elif name == 'layers':
        # Stack of layer colors
        colors = ['#e53e3e', '#dd6b20', '#38a169', '#3182ce']
        for i, c in enumerate(colors):
            p.setPen(QtGui.QPen(QtGui.QColor('#2d3748'), 1))
            p.setBrush(QtGui.QBrush(QtGui.QColor(c)))
            pts = [
                QtCore.QPoint(size // 2, 4 + i * 6),
                QtCore.QPoint(size - 4, 8 + i * 6),
                QtCore.QPoint(size // 2, 12 + i * 6),
                QtCore.QPoint(4, 8 + i * 6),
            ]
            p.drawPolygon(pts)

    elif name == 'measure':
        # Dimension caliper / ruler
        p.setPen(QtGui.QPen(QtGui.QColor('#d69e2e'), 2))
        p.drawLine(5, size // 2, size - 5, size // 2)
        p.drawLine(5, size // 2 - 5, 5, size // 2 + 5)
        p.drawLine(size - 5, size // 2 - 5, size - 5, size // 2 + 5)
        p.drawLine(size // 2, size // 2 - 3, size // 2, size // 2 + 3)

    elif name == 'gpu':
        # GPU graphics card / chip
        p.setPen(QtGui.QPen(QtGui.QColor('#2d3748'), 1.5))
        p.setBrush(QtGui.QBrush(QtGui.QColor('#38a169')))
        p.drawRoundedRect(7, 7, size - 14, size - 14, 2, 2)
        p.setBrush(QtGui.QBrush(QtGui.QColor('#48bb78')))
        p.drawRect(11, 11, size - 22, size - 22)
        p.setPen(QtGui.QPen(QtGui.QColor('#ecc94b'), 1.5))
        for k in range(9, size - 8, 4):
            p.drawLine(k, 3, k, 6)
            p.drawLine(k, size - 6, k, size - 3)
            p.drawLine(3, k, 6, k)
            p.drawLine(size - 6, k, size - 3, k)

    elif name == 'orbit':
        # 3D Orbit circle around sphere
        p.setPen(QtGui.QPen(QtGui.QColor('#3182ce'), 1.5))
        p.setBrush(QtGui.QBrush(QtGui.QColor('#63b3ed')))
        p.drawEllipse(size // 2 - 4, size // 2 - 4, 8, 8)
        p.setBrush(QtCore.Qt.NoBrush)
        p.setPen(QtGui.QPen(QtGui.QColor('#2b6cb0'), 1.5, QtCore.Qt.DashLine))
        p.drawEllipse(4, 4, size - 8, size - 8)

    elif name == 'look':
        # First-person eye looking
        p.setPen(QtGui.QPen(QtGui.QColor('#2b6cb0'), 2))
        p.setBrush(QtCore.Qt.NoBrush)
        p.drawArc(4, 6, size - 8, size - 12, 30 * 16, 120 * 16)
        p.drawArc(4, 6, size - 8, size - 12, 210 * 16, 120 * 16)
        p.setBrush(QtGui.QBrush(QtGui.QColor('#3182ce')))
        p.drawEllipse(size // 2 - 3, size // 2 - 3, 6, 6)

    elif name == 'app_logo':
        # 3D PlantView Logo (Industrial plant silhouette + 3D cube)
        grad = QtGui.QLinearGradient(0, 0, size, size)
        grad.setColorAt(0.0, QtGui.QColor('#0078d4'))
        grad.setColorAt(1.0, QtGui.QColor('#004578'))
        p.setBrush(QtGui.QBrush(grad))
        p.setPen(QtCore.Qt.NoPen)
        p.drawRoundedRect(2, 2, size - 4, size - 4, 4, 4)
        
        # White "PV" text
        p.setPen(QtGui.QPen(QtGui.QColor('white')))
        font = QtGui.QFont('Segoe UI', int(size * 0.42), QtGui.QFont.Bold)
        p.setFont(font)
        p.drawText(QtCore.QRect(0, 0, size, size), QtCore.Qt.AlignCenter, 'PV')

    else:
        # Generic dot
        p.setPen(QtCore.Qt.NoPen)
        p.setBrush(QtGui.QBrush(QtGui.QColor('#718096')))
        p.drawEllipse(6, 6, size - 12, size - 12)

    p.end()
    return QtGui.QIcon(pix)

