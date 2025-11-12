from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, QTimer, QRectF
from PySide6.QtGui import QPainter, QColor, QBrush, QPen


class GlowIndicator(QWidget):
    """A small glowing dot for live system status indicators."""
    def __init__(self, color="gray", parent=None):
        super().__init__(parent)
        self._color = QColor(color)
        self._pulse = 0.0
        self._growing = True
        self._enabled = True
        self.setFixedSize(20, 20)

        # Smooth glow animation
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._updatePulse)
        self.timer.start(40)

    def _updatePulse(self):
        if not self._enabled:
            return
        step = 0.07
        if self._growing:
            self._pulse += step
            if self._pulse >= 1.0:
                self._pulse = 1.0
                self._growing = False
        else:
            self._pulse -= step
            if self._pulse <= 0.4:
                self._pulse = 0.4
                self._growing = True
        self.update()

    def setColor(self, color):
        """Set indicator glow color (CSS-style name or QColor)."""
        if isinstance(color, QColor):
            self._color = color
        else:
            self._color = QColor(color)
        self.update()

    def setEnabled(self, enabled: bool):
        self._enabled = enabled
        if not enabled:
            self.timer.stop()
        else:
            if not self.timer.isActive():
                self.timer.start(40)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)

        rect = self.rect()
        radius = rect.width() / 2

        # Glow halo
        glow = QColor(self._color)
        glow.setAlphaF(0.35 * self._pulse)
        painter.setBrush(QBrush(glow))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(QRectF(0, 0, rect.width(), rect.height()))

        # Core dot
        core = QColor(self._color)
        core.setAlphaF(0.9)
        painter.setBrush(QBrush(core))
        painter.setPen(QPen(Qt.black, 1))
        painter.drawEllipse(QRectF(radius / 2, radius / 2, radius, radius))

        painter.end()
