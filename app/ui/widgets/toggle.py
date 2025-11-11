from PySide6.QtCore import Qt, QEasingCurve, QPropertyAnimation, QRectF, QSize
from PySide6.QtGui import QColor, QPainter, QPen, QBrush
from PySide6.QtWidgets import QCheckBox
from PySide6.QtCore import Property

class Toggle(QCheckBox):
    def __init__(self, parent=None, *, on_text="", off_text=""):
        super().__init__(parent)
        self._shift = 0.0
        self._anim = QPropertyAnimation(self, b"shift", self)
        self._anim.setDuration(140)
        self._anim.setEasingCurve(QEasingCurve.InOutQuad)
        self._on_text = on_text
        self._off_text = off_text
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedSize(54, 28)
        self.toggled.connect(self._start)

    def sizeHint(self):
        return QSize(54, 28)

    def _start(self, checked):
        self._anim.stop()
        self._anim.setStartValue(self._shift)
        self._anim.setEndValue(1.0 if checked else 0.0)
        self._anim.start()

    def getShift(self): return self._shift
    def setShift(self, v): self._shift = v; self.update()
    shift = Property(float, getShift, setShift)

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, True)
        rect = self.rect().adjusted(1, 5, -1, -5)

        # Track
        bg_on = QColor("#3a5bfd")
        bg_off = QColor("#2a2f3f")
        bg = bg_on if self.isChecked() else bg_off
        p.setBrush(QBrush(bg))
        p.setPen(Qt.NoPen)
        p.drawRoundedRect(rect, rect.height()/2, rect.height()/2)

        # Knob
        d = rect.height()-6
        x = rect.left()+3 + (rect.width()-d-6)*self._shift
        knob = QRectF(x, rect.top()+3, d, d)
        p.setBrush(QColor("#e6e6e6"))
        p.setPen(QPen(QColor("#141821"), 1))
        p.drawEllipse(knob)
