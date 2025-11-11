from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QLabel, QFrame
from .win_blur import enable_acrylic

class TitleBar(QFrame):
    def __init__(self, parent=None, title="QrsTweaks Suite"):
        super().__init__(parent)
        self.setObjectName("TitleBar")
        self.setFixedHeight(40)
        self._mouse_pos = None

        self.setStyleSheet("""
        #TitleBar { background: transparent; }
        QPushButton#WinBtn { border: none; padding: 6px; border-radius: 6px; }
        QPushButton#WinBtn:hover { background: rgba(255,255,255,0.08); }
        """)

        h = QHBoxLayout(self); h.setContentsMargins(8, 6, 8, 6); h.setSpacing(6)
        self.lbl = QLabel(title, self)
        self.lbl.setStyleSheet("color:#e6e6e6; font-weight:600;")
        self.lbl.setAttribute(Qt.WA_TransparentForMouseEvents)
        h.addWidget(self.lbl); h.addStretch()

        self.btn_min = QPushButton("–", self); self.btn_min.setObjectName("WinBtn")
        self.btn_max = QPushButton("□", self); self.btn_max.setObjectName("WinBtn")
        self.btn_close = QPushButton("✕", self); self.btn_close.setObjectName("WinBtn")
        h.addWidget(self.btn_min); h.addWidget(self.btn_max); h.addWidget(self.btn_close)

        self.btn_min.clicked.connect(lambda: self.window().showMinimized())
        self.btn_max.clicked.connect(self._toggle_max)
        self.btn_close.clicked.connect(self.window().close)

    def _toggle_max(self):
        w = self.window()
        if w.isMaximized(): w.showNormal()
        else: w.showMaximized()

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self._mouse_pos = e.globalPosition().toPoint() - self.window().frameGeometry().topLeft()
            e.accept()

    def mouseMoveEvent(self, e):
        if self._mouse_pos and e.buttons() & Qt.LeftButton:
            self.window().move(e.globalPosition().toPoint() - self._mouse_pos)
            e.accept()

    def mouseReleaseEvent(self, e):
        self._mouse_pos = None
        super().mouseReleaseEvent(e)

class FramelessWindow(QWidget):
    def __init__(self, central: QWidget, parent=None):
        super().__init__(parent)
        self.setWindowTitle("QrsTweaks — Local Suite")
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)

        outer = QVBoxLayout(self); outer.setContentsMargins(8, 8, 8, 8); outer.setSpacing(0)
        self.chrome = QFrame(self); self.chrome.setObjectName("Chrome")
        self.chrome.setStyleSheet("""
        #Chrome { background: rgba(15,17,21,210); border-radius: 14px; border: 1px solid #20263a; }
        """)
        outer.addWidget(self.chrome)

        v = QVBoxLayout(self.chrome); v.setContentsMargins(8, 8, 8, 8); v.setSpacing(8)
        self.title = TitleBar(self.chrome); v.addWidget(self.title)
        v.addWidget(central, 1)

    def showEvent(self, e):
    super().showEvent(e)
    if not hasattr(self, "_blur_applied"):
        try:
            hwnd = int(self.winId())
            enable_acrylic(hwnd, 0xAA18202B, acrylic=True)
            self._blur_applied = True
        except Exception:
            pass

