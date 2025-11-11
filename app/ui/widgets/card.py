from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter, QColor, QPen
from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel

class Card(QFrame):
    def __init__(self, title: str = "", parent=None, glow=False):
        super().__init__(parent)
        self.setObjectName("Card")
        if glow:
            self.setProperty("glow", "true")
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(14, 12, 14, 14)
        if title:
            t = QLabel(title, self); t.setProperty("cardTitle", "true")
            self._layout.addWidget(t)

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(14, 12, 14, 14)
        if title:
            t = QLabel(title, self); t.setProperty("cardTitle", "true")
            self._layout.addWidget(t)

    def body(self): return self._layout
