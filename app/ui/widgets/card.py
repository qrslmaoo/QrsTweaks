from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter, QColor, QPen
from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel

class Card(QFrame):
    def __init__(self, title: str = "", parent=None):
        super().__init__(parent)
        self._title = title
        self.setObjectName("Card")
        self.setStyleSheet("""
        #Card { background: rgba(21, 26, 36, 180); border: 1px solid #232838; border-radius: 12px; }
        #Card QLabel[cardTitle="true"] { color: #dfe3ea; font-weight: 600; letter-spacing: 0.2px; }
        """)
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(14, 12, 14, 14)
        if title:
            t = QLabel(title, self); t.setProperty("cardTitle", "true")
            self._layout.addWidget(t)

    def body(self): return self._layout
