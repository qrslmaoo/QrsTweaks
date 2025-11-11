from PySide6.QtCore import Qt, QPropertyAnimation
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QStackedWidget, QFrame, QLabel
)
from PySide6.QtGui import QIcon
from pathlib import Path

from .frameless_window import FramelessWindow


ROOT = Path(__file__).resolve().parents[2]
ICON_DIR = ROOT / "assets" / "icons"


class SidebarButton(QPushButton):
    def __init__(self, icon: str, text: str, index: int, controller):
        super().__init__(text)
        self.index = index
        self.controller = controller

        self.setCursor(Qt.PointingHandCursor)
        self.setCheckable(True)
        self.setIcon(QIcon(str(ICON_DIR / icon)))
        self.setIconSize(self.iconSize())

        self.setStyleSheet("""
QPushButton {
    background: transparent;
    border: none;
    padding: 12px 16px;
    text-align: left;
    color: #AAB0BD;
    font-size: 11pt;
    border-radius: 10px;
    font-weight: 500;
}
QPushButton:hover {
    background: rgba(110,140,255,0.08);
}
QPushButton:checked {
    background: rgba(110,140,255,0.22);
    color: #ffffff;
}
""")


    def iconSize(self):
        from PySide6.QtCore import QSize
        return QSize(20, 20)

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        self.controller.switch_page(self.index)


class SuiteWindow(FramelessWindow):
    def __init__(self, windows_page: QWidget, games_page: QWidget, passwords_page: QWidget):
        # Build the central widget FIRST
        central = QWidget()
        super().__init__(central_widget=central)

        main = QHBoxLayout(central)
        main.setContentsMargins(6, 6, 6, 6)
        main.setSpacing(8)

        # ========== SIDEBAR ==========
        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        sidebar.setStyleSheet("""
#Sidebar {
    background: #11131A;
    border-radius: 18px;
    border: 1px solid #20242F;
}
""")


        sb = QVBoxLayout(sidebar)
        sb.setContentsMargins(10, 10, 10, 10)
        sb.setSpacing(6)

        self.buttons = []
        self.stack = QStackedWidget()

        entries = [
            ("os.svg", "Windows Optimizer", windows_page),
            ("gamepad.svg", "Game Optimizer", games_page),
            ("lock.svg", "Password Manager", passwords_page),
        ]

        # Build sidebar buttons + stack pages
        for i, (icon, text, page) in enumerate(entries):
            btn = SidebarButton(icon, text, i, controller=self)
            self.buttons.append(btn)
            sb.addWidget(btn)
            self.stack.addWidget(page)

        sb.addStretch()

        # Optional settings button (disabled for now)
        settings_btn = SidebarButton("settings.svg", "Settings", len(entries), controller=self)
        settings_btn.setEnabled(False)
        sb.addWidget(settings_btn)

        # ========== MAIN AREA ==========
        main.addWidget(sidebar)
        main.addWidget(self.stack, 1)

        # Default selection
        self.buttons[0].setChecked(True)
        self.stack.setCurrentIndex(0)

    # ========== PAGE SWITCHING WITH FADE ANIMATION ==========
    def switch_page(self, index: int):
        for b in self.buttons:
            b.setChecked(False)
        if index < len(self.buttons):
            self.buttons[index].setChecked(True)

        new_page = self.stack.widget(index)
        new_page.setWindowOpacity(0.0)

        # Prevent memory leak: store animations
        if not hasattr(self, "_animations"):
            self._animations = []

        anim = QPropertyAnimation(new_page, b"windowOpacity", self)
        anim.setDuration(160)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.start()

        # Retain reference
        self._animations.append(anim)
        if len(self._animations) > 20:
            self._animations.pop(0)

        self.stack.setCurrentIndex(index)
