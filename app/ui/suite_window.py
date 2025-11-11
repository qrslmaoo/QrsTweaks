import os
from pathlib import Path
from PySide6.QtCore import Qt, QPropertyAnimation
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QFrame, QPushButton, QStackedWidget, QLabel, QSizePolicy

from .frameless_window import FramelessWindow
from .widgets.card import Card

ROOT = Path(__file__).resolve().parents[2]
ICON = ROOT / "assets" / "icons"

class IconButton(QPushButton):
    def __init__(self, icon_path: Path, text: str, index: int, controller, parent=None):
        super().__init__(text, parent)
        self.index = index
        self.controller = controller
        self.setCursor(Qt.PointingHandCursor)
        self.setCheckable(True)
        self.setStyleSheet("""
        QPushButton {
            background: transparent; color: #cfd3dd; border: none; padding: 10px 12px; text-align: left;
        }
        QPushButton:checked { background: rgba(58,91,253,0.17); border-radius: 8px; color: #ffffff; }
        QPushButton:hover { background: rgba(255,255,255,0.06); border-radius: 8px; }
        """)
        if icon_path.exists():
            self.setIcon(QIcon(str(icon_path)))
        self.setIconSize(self.iconSize())

    def iconSize(self):  # consistent icon size
        from PySide6.QtCore import QSize
        return QSize(22, 22)

    def mousePressEvent(self, e):
        super().mousePressEvent(e)
        self.controller.switch_page(self.index)

class SuiteWindow(FramelessWindow):
    def __init__(self, windows_widget: QWidget, games_widget: QWidget, passwords_widget: QWidget, parent=None):
        # central content
        central = QWidget()
        super().__init__(central, parent=parent)

        layout = QHBoxLayout(central); layout.setContentsMargins(6, 6, 6, 6); layout.setSpacing(10)

        # Sidebar
        sidebar = QFrame(); sidebar.setObjectName("Sidebar")
        sidebar.setStyleSheet("#Sidebar { background: rgba(13,15,20,165); border: 1px solid #20263a; border-radius: 12px; }")
        sb = QVBoxLayout(sidebar); sb.setContentsMargins(10, 10, 10, 10); sb.setSpacing(6)

        self.btns = []
        entries = [
            ("os.svg", "Windows Optimizer", windows_widget),
            ("gamepad.svg", "Game Optimizer", games_widget),
            ("lock.svg", "Password Manager", passwords_widget),
        ]
        self.stack = QStackedWidget()

        for i, (icon, text, page) in enumerate(entries):
            b = IconButton(ICON / icon, text, i, controller=self)
            self.btns.append(b); sb.addWidget(b)
            self.stack.addWidget(page)

        sb.addStretch()
        # Optional settings button
        settings = IconButton(ICON / "settings.svg", "Settings", len(entries), controller=self)
        settings.setEnabled(False)  # placeholder
        sb.addWidget(settings)

        layout.addWidget(sidebar)
        layout.addWidget(self.stack, 1)

        # Select first
        self.btns[0].setChecked(True)
        self.stack.setCurrentIndex(0)

    def switch_page(self, index: int):
        for b in self.btns: b.setChecked(False)
        if index < len(self.btns):
            self.btns[index].setChecked(True)

        if not hasattr(self, "_anims"):
    self._anims = []

new = self.stack.widget(index)
new.setWindowOpacity(0.0)

anim = QPropertyAnimation(new, b"windowOpacity", self)
anim.setDuration(160)
anim.setStartValue(0.0)
anim.setEndValue(1.0)
anim.start()

self._anims.append(anim)

# cap list size
if len(self._anims) > 20:
    self._anims.pop(0)

