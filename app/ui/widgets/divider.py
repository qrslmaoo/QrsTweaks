# app/ui/widgets/divider.py
from PySide6.QtWidgets import QWidget, QLabel, QHBoxLayout, QFrame
from PySide6.QtCore import Qt

class Divider(QWidget):
    """A clean horizontal divider with a centered label."""
    def __init__(self, text="", parent=None):
        super().__init__(parent)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 12, 0, 12)
        layout.setSpacing(10)

        # Left line
        left = QFrame()
        left.setFrameShape(QFrame.HLine)
        left.setFrameShadow(QFrame.Sunken)
        left.setStyleSheet("color: rgba(180,180,200,0.25);")
        layout.addWidget(left)

        # Label
        if text:
            label = QLabel(text)
            label.setStyleSheet(
                "color:#DDE1EA; font-size:12pt; font-weight:600;"
            )
            layout.addWidget(label)

        # Right line
        right = QFrame()
        right.setFrameShape(QFrame.HLine)
        right.setFrameShadow(QFrame.Sunken)
        right.setStyleSheet("color: rgba(180,180,200,0.25);")
        layout.addWidget(right)
