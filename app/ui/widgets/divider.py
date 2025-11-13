# app/ui/widgets/divider.py
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QFrame
from PySide6.QtCore import Qt

class Divider(QWidget):
    """
    A clean horizontal section divider with centered text:

       -------  Section Name  -------

    Matches QrsTweaks dark theme exactly.
    """

    def __init__(self, text: str = "", parent=None):
        super().__init__(parent)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 20, 0, 10)
        layout.setSpacing(12)

        # Left line
        left = QFrame()
        left.setFrameShape(QFrame.HLine)
        left.setFrameShadow(QFrame.Sunken)
        left.setStyleSheet("color: rgba(255,255,255,0.10);")
        layout.addWidget(left, 1)

        # Title text (centered)
        label = QLabel(text)
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("""
            color: #DDE1EA;
            font-size: 13pt;
            font-weight: 600;
        """)
        layout.addWidget(label)

        # Right line
        right = QFrame()
        right.setFrameShape(QFrame.HLine)
        right.setFrameShadow(QFrame.Sunken)
        right.setStyleSheet("color: rgba(255,255,255,0.10);")
        layout.addWidget(right, 1)
