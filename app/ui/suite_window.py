# app/ui/suite_window.py

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QStackedWidget,
    QApplication,
    QLabel,
)
from PySide6.QtCore import Qt, QTimer

from app.ui.frameless_window import FramelessWindow
from app.pages.dashboard_page import DashboardPage
from app.pages.windows_page import WindowsPage
from app.pages.games_page import GamesPage
from app.pages.passwords_page import PasswordsPage
from app.pages.timeline_page import TimelinePage
from src.qrs.core.log_manager import log_mgr


class SuiteWindow(FramelessWindow):
    def __init__(self, parent=None):
        super().__init__(parent)

        # ----------------------------------------
        # Default window size and minimums
        # ----------------------------------------
        self.resize(1200, 620)
        self.setMinimumSize(1000, 580)

        # ----------------------------------------
        # Root layout: sidebar + right container
        # ----------------------------------------
        root_layout = QHBoxLayout(self.center)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # ----------------------------------------
        # Sidebar setup
        # ----------------------------------------
        self.sidebar = QWidget()
        self.sidebar.setFixedWidth(210)
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
                background-color: rgba(196, 72, 255, 0.28);
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
        self.btn_timeline = QPushButton("Timeline")

        for b in (self.btn_dash, self.btn_win, self.btn_games, self.btn_pass, self.btn_timeline):
            b.setCheckable(True)
            side_layout.addWidget(b)

        side_layout.addStretch()
        root_layout.addWidget(self.sidebar)

        # ----------------------------------------
        # Right container: status bar + stack
        # ----------------------------------------
        right_container = QWidget()
        right_layout = QVBoxLayout(right_container)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        # ---------- Global status bar ----------
        self.status_bar = QWidget()
        self.status_bar.setFixedHeight(32)
        self.status_bar.setStyleSheet(
            """
            QWidget {
                background-color: rgba(14,16,22,0.96);
                border-top-right-radius: 10px;
            }
            """
        )

        status_layout = QHBoxLayout(self.status_bar)
        status_layout.setContentsMargins(12, 4, 12, 4)
        status_layout.setSpacing(8)

        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("color: #DDE1EA; font-size: 9pt;")
        self.status_label.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)

        self.status_context_label = QLabel("Page: Dashboard")
        self.status_context_label.setStyleSheet("color: #7F8A99; font-size: 9pt;")
        self.status_context_label.setAlignment(Qt.AlignVCenter | Qt.AlignRight)

        status_layout.addWidget(self.status_label, stretch=2)
        status_layout.addStretch(1)
        status_layout.addWidget(self.status_context_label, stretch=1)

        right_layout.addWidget(self.status_bar)

        # ---------- Central stacked area ----------
        self.stack = QStackedWidget()
        right_layout.addWidget(self.stack)
        root_layout.addWidget(right_container)

        # ----------------------------------------
        # Instantiate pages once
        # ----------------------------------------
        self.page_dash = DashboardPage()
        self.page_win = WindowsPage()
        self.page_games = GamesPage()
        self.page_pass = PasswordsPage()
        self.page_timeline = TimelinePage()

        self.stack.addWidget(self.page_dash)      # index 0
        self.stack.addWidget(self.page_win)       # index 1
        self.stack.addWidget(self.page_games)     # index 2
        self.stack.addWidget(self.page_pass)      # index 3
        self.stack.addWidget(self.page_timeline)  # index 4

        # ----------------------------------------
        # Button connections
        # ----------------------------------------
        self.btn_dash.clicked.connect(lambda: self._switch_page(0))
        self.btn_win.clicked.connect(lambda: self._switch_page(1))
        self.btn_games.clicked.connect(lambda: self._switch_page(2))
        self.btn_pass.clicked.connect(lambda: self._switch_page(3))
        self.btn_timeline.clicked.connect(lambda: self._switch_page(4))

        self.btn_dash.setChecked(True)
        self.stack.setCurrentIndex(0)

        # Initial status
        self.set_status("Dashboard ready.", level="info")
        self._update_context_label(0)

        # Hook global status handler into LogManager
        log_mgr.set_status_handler(self._status_from_log)

        # Delay re-layout slightly to ensure all child pages are fully sized
        QTimer.singleShot(300, self._initial_layout_fix)

    # ---------------------------------------------------
    # Global status helpers
    # ---------------------------------------------------
    def set_status(self, text: str, level: str = "info") -> None:
        """
        Update the global status bar message.

        level: "info", "ok", "warn", "error"
        """
        colors = {
            "info": "#DDE1EA",
            "ok": "#4ED97A",
            "warn": "#F0C674",
            "error": "#FF5C5C",
        }
        color = colors.get(level.lower(), "#DDE1EA")
        self.status_label.setStyleSheet(f"color: {color}; font-size: 9pt;")
        self.status_label.setText(text)

    def _status_from_log(self, level: str, message: str) -> None:
        """
        Called by LogManager when an entry is logged with bubble=True.
        """
        self.set_status(message, level=level)

    def _update_context_label(self, index: int) -> None:
        names = {
            0: "Dashboard",
            1: "Windows Optimizer",
            2: "Game Optimizer",
            3: "Password Manager",
            4: "Timeline",
        }
        name = names.get(index, "Unknown")
        self.status_context_label.setText(f"Page: {name}")

    # ---------------------------------------------------
    # Page switching
    # ---------------------------------------------------
    def _switch_page(self, index: int) -> None:
        for b in (self.btn_dash, self.btn_win, self.btn_games, self.btn_pass, self.btn_timeline):
            b.setChecked(False)

        (self.btn_dash, self.btn_win, self.btn_games, self.btn_pass, self.btn_timeline)[
            index
        ].setChecked(True)

        self._force_reflow()
        QApplication.processEvents()

        self.stack.setCurrentIndex(index)
        self._update_context_label(index)

        if index == 0:
            self.set_status("Dashboard ready.", level="info")
        elif index == 1:
            self.set_status("Windows optimizer ready.", level="ok")
        elif index == 2:
            self.set_status("Game optimizer ready. Launch your game first.", level="info")
        elif index == 3:
            self.set_status("Password vault ready.", level="info")
        elif index == 4:
            self.set_status("Timeline view active.", level="info")

        QTimer.singleShot(50, self._force_reflow)

    # ---------------------------------------------------
    # Layout reflow helpers
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
        self.resize(self.size())
        QApplication.processEvents()

    def _initial_layout_fix(self) -> None:
        self._force_reflow()
        self.adjustSize()
        self.resize(self.sizeHint())
        self.update()
        QApplication.processEvents()

    # ---------------------------------------------------
    # Resize event hook
    # ---------------------------------------------------
    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        QTimer.singleShot(30, self._force_reflow)
