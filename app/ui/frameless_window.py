from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QLabel, QFrame

from .win_blur import enable_acrylic


class TitleBar(QFrame):
    def __init__(self, parent=None, title="QrsTweaks Suite"):
        super().__init__(parent)

        self.setObjectName("TitleBar")
        self.setFixedHeight(40)
        self._drag_pos = None

        self.setStyleSheet("""
        #TitleBar {
            background: transparent;
        }
        QPushButton#WinBtn {
            border: none;
            padding: 6px;
            border-radius: 6px;
        }
        QPushButton#WinBtn:hover {
            background: rgba(255,255,255,0.1);
        }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(6)

        self.title = QLabel(title)
        self.title.setStyleSheet("color: #e6e6e6; font-size: 11pt; font-weight: 600;")
        self.title.setAttribute(Qt.WA_TransparentForMouseEvents)
        layout.addWidget(self.title)
        layout.addStretch()

        # Window control buttons
        self.btn_min = QPushButton("–")
        self.btn_min.setObjectName("WinBtn")

        self.btn_max = QPushButton("□")
        self.btn_max.setObjectName("WinBtn")

        self.btn_close = QPushButton("✕")
        self.btn_close.setObjectName("WinBtn")

        layout.addWidget(self.btn_min)
        layout.addWidget(self.btn_max)
        layout.addWidget(self.btn_close)

        # Connect actions
        self.btn_min.clicked.connect(self._minimize)
        self.btn_max.clicked.connect(self._maximize)
        self.btn_close.clicked.connect(self._close)

    def _minimize(self):
        self.window().showMinimized()

    def _maximize(self):
        w = self.window()
        if w.isMaximized():
            w.showNormal()
        else:
            w.showMaximized()

    def _close(self):
        self.window().close()

    # Drag behavior
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.window().frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if self._drag_pos and event.buttons() & Qt.LeftButton:
            self.window().move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        self._drag_pos = None
        super().mouseReleaseEvent(event)


class FramelessWindow(QWidget):
    def __init__(self, central_widget: QWidget, parent=None):
        super().__init__(parent)

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        self.setAttribute(Qt.WA_TranslucentBackground)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(8, 8, 8, 8)

        self._chrome = QFrame()
        self._chrome.setObjectName("Chrome")
        self._chrome.setStyleSheet("""
        #Chrome {
            background: rgba(15, 17, 21, 255);
            border-radius: 14px;
            border: 1px solid #20263a;
        }
        """)

        outer.addWidget(self._chrome)

        chrome_layout = QVBoxLayout(self._chrome)
        chrome_layout.setContentsMargins(8, 8, 8, 8)

        # Titlebar + content
        self.title_bar = TitleBar(self._chrome)
        chrome_layout.addWidget(self.title_bar)
        chrome_layout.addWidget(central_widget, 1)

        # Apply blur ONCE
        self._blur_applied = False

    def showEvent(self, event):
        super().showEvent(event)
        if not self._blur_applied:
            try:
                hwnd = int(self.winId())
                enable_acrylic(hwnd, 0xAA18202B, acrylic=False)
            except Exception:
                pass
            self._blur_applied = True
