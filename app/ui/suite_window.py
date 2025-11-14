# app/ui/suite_window.py

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QStackedWidget,
    QApplication,
)
from PySide6.QtCore import Qt, QTimer, QSize

from app.ui.frameless_window import FramelessWindow
from app.pages.dashboard_page import DashboardPage
from app.pages.windows_page import WindowsPage
from app.pages.games_page import GamesPage
from app.pages.passwords_page import PasswordsPage
from app.pages.service_page import ServicePage


class SuiteWindow(FramelessWindow):
    def __init__(self, parent=None):
        super().__init__(parent)

        # ----------------------------------------
        # Default window size and minimums
        # ----------------------------------------
        self.resize(1200, 620)  # width x height
        self.setMinimumSize(1000, 580)  # smaller baseline

        layout = QHBoxLayout(self.center)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ----------------------------------------
        # Sidebar
        # ----------------------------------------
        self.sidebar = QWidget()
        self.sidebar.setFixedWidth(200)
        self.sidebar.setStyleSheet(
            """
            QWidget {
                background-color: rgba(10,10,14,0.88);
                border-top-left-radius: 10px;
                border-bottom-left-radius: 10px;
            }
            QPushButton {
                background-color: transparent;
                color: #DDE1EA;
                border-radius: 8px;
                padding: 8px 12px;
                text-align: left;
                font-size: 10pt;
            }
            QPushButton:hover {
                background-color: rgba(255,255,255,0.08);
            }
            QPushButton:checked {
                background-color: rgba(255,255,255,0.18);
                font-weight: 600;
            }
            """
        )

        side_layout = QVBoxLayout(self.sidebar)
        side_layout.setContentsMargins(8, 12, 8, 12)
        side_layout.setSpacing(4)

        self.btn_dash = QPushButton("Dashboard")
        self.btn_win = QPushButton("Windows Optimizer")
        self.btn_games = QPushButton("Games")
        self.btn_pass = QPushButton("Passwords")
        self.btn_service = QPushButton("Service / Daemon")

        self._nav_buttons = (
            self.btn_dash,
            self.btn_win,
            self.btn_games,
            self.btn_pass,
            self.btn_service,
        )

        for b in self._nav_buttons:
            b.setCheckable(True)
            side_layout.addWidget(b)

        side_layout.addStretch()
        layout.addWidget(self.sidebar)

        # ----------------------------------------
        # Central stacked area
        # ----------------------------------------
        self.stack = QStackedWidget()
        layout.addWidget(self.stack)

        # Instantiate pages once
        self.page_dash = DashboardPage()
        self.page_win = WindowsPage()
        self.page_games = GamesPage()
        self.page_pass = PasswordsPage()
        self.page_service = ServicePage()

        self.stack.addWidget(self.page_dash)     # index 0
        self.stack.addWidget(self.page_win)      # index 1
        self.stack.addWidget(self.page_games)    # index 2
        self.stack.addWidget(self.page_pass)     # index 3
        self.stack.addWidget(self.page_service)  # index 4

        # Button connections
        self.btn_dash.clicked.connect(lambda: self._switch_page(0))
        self.btn_win.clicked.connect(lambda: self._switch_page(1))
        self.btn_games.clicked.connect(lambda: self._switch_page(2))
        self.btn_pass.clicked.connect(lambda: self._switch_page(3))
        self.btn_service.clicked.connect(lambda: self._switch_page(4))

        # Default page = Dashboard
        self.btn_dash.setChecked(True)
        self.stack.setCurrentIndex(0)

        # Delay re-layout slightly to ensure all child pages are fully sized
        QTimer.singleShot(300, self._initial_layout_fix)

    # ---------------------------------------------------
    # Page switching
    # ---------------------------------------------------
    def _switch_page(self, index: int) -> None:
        # Update checked state
        for i, b in enumerate(self._nav_buttons):
            b.setChecked(i == index)

        # Force resize + reflow before switch
        self._force_reflow()
        QApplication.processEvents()

        self.stack.setCurrentIndex(index)

        # Delay again slightly to ensure the switch is rendered cleanly
        QTimer.singleShot(50, self._force_reflow)

    # ---------------------------------------------------
    # Fix layout reflow issues
    # ---------------------------------------------------
    def _force_reflow(self) -> None:
        self.stack.setMinimumSize(1, 1)
        self.stack.adjustSize()

        for i in range(self.stack.count()):
            w = self.stack.widget(i)
            if w:
                w.adjustSize()
                w.updateGeometry()

        self.center.updateGeometry()
        self.updateGeometry()
        self.resize(self.size())  # Forces internal geometry sync
        QApplication.processEvents()

    # ---------------------------------------------------
    # Initial window layout on startup
    # ---------------------------------------------------
    def _initial_layout_fix(self) -> None:
        """Ensures proper geometry when window first shows."""
        self._force_reflow()
        self.adjustSize()
        self.resize(self.sizeHint())
        self.update()
        QApplication.processEvents()

    # ---------------------------------------------------
    # Resize event hook
    # ---------------------------------------------------
    def resizeEvent(self, event) -> None:
        """Guarantees children expand fully after resize."""
        super().resizeEvent(event)
        QTimer.singleShot(30, self._force_reflow)
