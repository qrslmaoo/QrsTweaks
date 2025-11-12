from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
)
from PySide6.QtCore import Qt, QEvent, QRectF
from PySide6.QtGui import QMouseEvent, QPainter, QColor, QPainterPath


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
                    color: #DDE1EA;
                    font-weight: 600;
                }
                QPushButton:hover {
                    background: rgba(255,255,255,0.18);
                }
            """)
            layout.addWidget(b)

        self.btn_close.clicked.connect(self.window().close)
        self.btn_min.clicked.connect(self.window().showMinimized)
        self.btn_max.clicked.connect(parent.toggle_max)

    # ---- Window dragging ----
    def mousePressEvent(self, e: QMouseEvent):
        if e.button() == Qt.LeftButton:
            self._drag_pos = e.globalPosition().toPoint() - self.window().frameGeometry().topLeft()

    def mouseMoveEvent(self, e: QMouseEvent):
        if self._drag_pos and (e.buttons() & Qt.LeftButton):
            self.window().move(e.globalPosition().toPoint() - self._drag_pos)

    def mouseReleaseEvent(self, e: QMouseEvent):
        self._drag_pos = None


class ChromeWidget(QWidget):
    """Painted translucent glass surface with tuned opacity for readability."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TranslucentBackground, False)
        self.setAutoFillBackground(False)
        self._radius = 12
        self._constructed = True

        # Appearance controls
        self._blur_alpha = 0.88     # previously 0.78 — less transparent
        self._base_color = QColor(22, 24, 30)

    def paintEvent(self, event):
        if not getattr(self, "_constructed", False):
            return

        painter = QPainter(self)
        if not painter.isActive():
            return
        painter.setRenderHint(QPainter.Antialiasing, True)

        # Fully clear surface first
        painter.setCompositionMode(QPainter.CompositionMode_Source)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 0))

        # Draw rounded translucent glass background
        painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
        path = QPainterPath()
        rect = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        path.addRoundedRect(rect, self._radius, self._radius)

        bg = QColor(self._base_color)
        bg.setAlphaF(self._blur_alpha)
        painter.fillPath(path, bg)

        # Subtle glowing edge border for depth
        border_color = QColor(255, 255, 255, 18)
        painter.setPen(border_color)
        painter.drawPath(path)

        painter.end()


class FramelessWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._constructed = False
        self._maximized = False

        # ---- Window flags ----
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowSystemMenuHint |
            Qt.WindowMinMaxButtonsHint
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAutoFillBackground(False)

        # ---- Root container ----
        container = QWidget(self)
        container.setObjectName("RootContainer")

        root = QVBoxLayout(container)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ---- Chrome layer ----
        self.chrome = ChromeWidget(self)
        chrome_layout = QVBoxLayout(self.chrome)
        chrome_layout.setContentsMargins(0, 0, 0, 0)
        chrome_layout.setSpacing(0)

        # Title bar
        self.titlebar = TitleBar(self)
        chrome_layout.addWidget(self.titlebar)

        # Central widget holder
        self.center = QWidget()
        self.center.setObjectName("Center")
        self.center.setStyleSheet("background: transparent;")
        chrome_layout.addWidget(self.center)

        root.addWidget(self.chrome)

        # Apply main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        main_layout.addWidget(container)

        self._constructed = True

    # ---- Maximize toggle ----
    def toggle_max(self):
        if not self._maximized:
            self._old_geometry = self.geometry()
            self.showMaximized()
            self._maximized = True
        else:
            self.showNormal()
            if hasattr(self, "_old_geometry"):
                self.setGeometry(self._old_geometry)
            self._maximized = False
        self.chrome.update()
        self.update()

    # ---- Resize safety ----
    def resizeEvent(self, event):
        if getattr(self, "_constructed", False):
            self.chrome.update()
        super().resizeEvent(event)

    # ---- Child safety ----
    def childEvent(self, event):
        try:
            if event and event.type() in (QEvent.ChildAdded, QEvent.ChildRemoved):
                self.chrome.update()
                self.update()
        except Exception:
            pass
        super().childEvent(event)
