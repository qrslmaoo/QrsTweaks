from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPainter, QColor, QPen
from PySide6.QtWidgets import QWidget

class GlowIndicator(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._t = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(16)  # ~60fps
        self.setFixedSize(72, 72)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)

    def _tick(self):
        self._t = (self._t + 3) % 360
        self.update()

    def paintEvent(self, e):
        p = QPainter(self); p.setRenderHint(QPainter.Antialiasing, True)
        w = self.width(); h = self.height(); r = min(w, h) / 2 - 6
        cx, cy = w/2, h/2

        # soft glow rings
        for i, a in enumerate((0.35, 0.22, 0.12)):
            p.setPen(QPen(QColor(90,125,255, int(255*a)), 6 - i*2))
            p.drawEllipse(int(cx-r)+i*3, int(cy-r)+i*3, int(2*r-i*6), int(2*r-i*6))

        # spinning arc
        p.setPen(QPen(QColor(90,125,255,220), 4, cap=Qt.RoundCap))
        p.drawArc(int(cx-r), int(cy-r), int(2*r), int(2*r), self._t*16, 80*16)
