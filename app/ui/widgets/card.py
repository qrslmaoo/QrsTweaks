from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel, QWidget
from PySide6.QtCore import Qt


class Card(QFrame):
    def __init__(self, title: str = "", parent=None):
        super().__init__(parent)
        self.setObjectName("Card")

        # ----- Outer card layout -----
        outer = QVBoxLayout(self)
        outer.setContentsMargins(16, 16, 16, 16)
        outer.setSpacing(10)

        # ----- Optional title -----
        if title:
            lbl = QLabel(title)
            lbl.setProperty("cardTitle", True)
            outer.addWidget(lbl, alignment=Qt.AlignLeft)

        # ------------------------------------------------------------
        # FIX: Create a proper container BEFORE adding the body layout.
        # This avoids Qt duplicating children inside ScrollAreas.
        # ------------------------------------------------------------
        self._body_container = QWidget()
        self._body_layout = QVBoxLayout(self._body_container)
        self._body_layout.setContentsMargins(0, 0, 0, 0)
        self._body_layout.setSpacing(10)

        outer.addWidget(self._body_container)

    def body(self):
        """Return the inner layout for adding widgets safely."""
        return self._body_layout
