# app/ui/suite_window.py
from shiboken6 import delete

from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout,
    QLabel, QPushButton, QScrollArea
)
from PySide6.QtCore import Qt

from app.ui.frameless_window import FramelessWindow
from app.pages.windows_page import WindowsPage
from app.pages.games_page import GamesPage
from app.pages.passwords_page import PasswordsPage


class SuiteWindow(FramelessWindow):
    def __init__(self, parent=None):
        super().__init__(parent)

        # ----------------------------------------------------------
        # MAIN LAYOUT
        # ----------------------------------------------------------
        root = QHBoxLayout(self.center)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ----------------------------------------------------------
        # SIDEBAR
        # ----------------------------------------------------------
        sidebar = QWidget(objectName="Sidebar")
        sidebar.setFixedWidth(220)
        sidebar.setStyleSheet("""
            #Sidebar {
                background: rgba(255,255,255,0.06);
            }
        """)

        sb = QVBoxLayout(sidebar)
        sb.setContentsMargins(12, 20, 12, 20)
        sb.setSpacing(12)

        title = QLabel("QrsTweaks Suite")
        title.setStyleSheet("color:#DDE1EA; font-size:14pt; font-weight:600;")
        sb.addWidget(title)
        sb.addSpacing(8)

        # Sidebar buttons
        self.btn_win = QPushButton("  Windows Optimizer")
        self.btn_games = QPushButton("  Games")
        self.btn_pass = QPushButton("  Passwords")

        for b in (self.btn_win, self.btn_games, self.btn_pass):
            b.setCursor(Qt.PointingHandCursor)
            b.setCheckable(True)
            b.setFixedHeight(40)
            b.setStyleSheet("""
                QPushButton {
                    text-align: left;
                    padding-left: 14px;
                    background: rgba(255,255,255,0.08);
                    color: #DDE1EA;
                    border-radius: 8px;
                    font-size: 11pt;
                }
                QPushButton:hover { background: rgba(255,255,255,0.16); }
                QPushButton:checked { background: rgba(255,255,255,0.24); }
            """)
            sb.addWidget(b)

        sb.addStretch()
        root.addWidget(sidebar)

        # ----------------------------------------------------------
        # SCROLL AREA
        # ----------------------------------------------------------
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll.setObjectName("ScrollArea")
        self.scroll.setStyleSheet("""
            QScrollArea { border: none; background: transparent; }

            QScrollBar:vertical {
                width: 10px;
                background: transparent;
            }
            QScrollBar::handle:vertical {
                background: rgba(255,255,255,0.20);
                border-radius: 5px;
            }
            QScrollBar::handle:vertical:hover {
                background: rgba(255,255,255,0.35);
            }
            QScrollBar::add-line, QScrollBar::sub-line {
                height: 0px;
            }
        """)
        root.addWidget(self.scroll, 1)

        # ----------------------------------------------------------
        # BUTTON CONNECTIONS
        # ----------------------------------------------------------
        self.btn_win.clicked.connect(lambda: self.load_page("win"))
        self.btn_games.clicked.connect(lambda: self.load_page("games"))
        self.btn_pass.clicked.connect(lambda: self.load_page("pass"))

        # ----------------------------------------------------------
        # LOAD DEFAULT PAGE
        # ----------------------------------------------------------
        self.load_page("win")

    # ===================================================================
    #           HARD DELETE TO PREVENT DUPLICATION + GHOST LAYERS
    # ===================================================================
    def _destroy_page(self):
        old = self.scroll.takeWidget()
        if old is not None:
            old.setParent(None)
            delete.delete(old)        # ✅ Immediate destruction (not delayed)
            return True
        return False

    # ===================================================================
    #                           LOAD PAGE
    # ===================================================================
    def load_page(self, key: str):

        # -------- DESTROY OLD PAGE IMMEDIATELY --------
        self._destroy_page()

        # -------- BUILD NEW PAGE --------
        if key == "win":
            page = WindowsPage()
            self.btn_win.setChecked(True)
            self.btn_games.setChecked(False)
            self.btn_pass.setChecked(False)

        elif key == "games":
            page = GamesPage()
            self.btn_win.setChecked(False)
            self.btn_games.setChecked(True)
            self.btn_pass.setChecked(False)

        else:
            page = PasswordsPage()
            self.btn_win.setChecked(False)
            self.btn_games.setChecked(False)
            self.btn_pass.setChecked(True)

        # -------- WRAP PAGE IN A CONTAINER --------
        container = QWidget()
        lay = QVBoxLayout(container)
        lay.setContentsMargins(20, 20, 20, 20)
        lay.setSpacing(20)
        lay.addWidget(page)
        lay.addStretch()

        # -------- INSERT INTO SCROLLAREA --------
        self.scroll.setWidget(container)
