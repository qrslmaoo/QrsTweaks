# app/ui/frameless_window.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame
)
from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QMouseEvent


class TitleBar(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self._drag_pos = None
        self.setFixedHeight(40)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 0, 12, 0)

        self.label = QLabel("QrsTweaks Suite")
        self.label.setStyleSheet("color:#DDE1EA; font-size:11pt; font-weight:600;")
        layout.addWidget(self.label)
        layout.addStretch()

        self.btn_min = QPushButton("-")
        self.btn_max = QPushButton("□")
        self.btn_close = QPushButton("✕")

        for b in (self.btn_min, self.btn_max, self.btn_close):
            b.setFixedSize(32, 32)
            b.setFlat(True)
            b.setStyleSheet("""
                QPushButton {
                    background: rgba(255,255,255,0.06);
                    border-radius: 6px;
                }
                QPushButton:hover {
                    background: rgba(255,255,255,0.15);
                }
            """)
            layout.addWidget(b)

        self.btn_close.clicked.connect(self.window().close)
        self.btn_min.clicked.connect(self.window().showMinimized)
        self.btn_max.clicked.connect(parent.toggle_max)

    # ===== DRAGGING REAL WINDOW =====
    def mousePressEvent(self, e: QMouseEvent):
        if e.button() == Qt.LeftButton:
            self._drag_pos = e.globalPosition().toPoint() - self.window().frameGeometry().topLeft()

    def mouseMoveEvent(self, e: QMouseEvent):
        if self._drag_pos and (e.buttons() & Qt.LeftButton):
            self.window().move(e.globalPosition().toPoint() - self._drag_pos)

    def mouseReleaseEvent(self, e: QMouseEvent):
        self._drag_pos = None


class FramelessWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        # ----------------------------------
        # BASIC WINDOW FLAGS
        # ----------------------------------
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowSystemMenuHint |
            Qt.WindowMinMaxButtonsHint
        )
        self.setAttribute(Qt.WA_TranslucentBackground)

        self._maximized = False

        # ----------------------------------
        # MAIN LAYOUT (chrome + content)
        # ----------------------------------
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        chrome = QWidget()
        chrome.setObjectName("Chrome")
        chrome.setStyleSheet("""
            #Chrome {
                background: rgba(20,20,24,0.70);
                border-radius: 12px;
            }
        """)

        chrome_layout = QVBoxLayout(chrome)
        chrome_layout.setContentsMargins(0, 0, 0, 0)
        chrome_layout.setSpacing(0)

        # Title bar
        self.titlebar = TitleBar(self)
        chrome_layout.addWidget(self.titlebar)

        # Content Container
        self.center = QWidget()
        self.center.setObjectName("Center")
        self.center.setStyleSheet("background: transparent;")
        chrome_layout.addWidget(self.center)

        root.addWidget(chrome)

    # =====================================================
    #         MAXIMIZE / RESTORE
    # =====================================================
    def toggle_max(self):
        if not self._maximized:
            self._old_geometry = self.geometry()
            self.showMaximized()
            self._maximized = True
        else:
            self.showNormal()
            self.setGeometry(self._old_geometry)
            self._maximized = False
