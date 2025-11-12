from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox
)
from PySide6.QtCore import Qt, QEvent, QRectF, Signal
from PySide6.QtGui import QMouseEvent, QPainter, QColor, QPainterPath


class TitleBar(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self._drag_pos = None
        self.setFixedHeight(44)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 0, 12, 0)
        layout.setSpacing(10)

        self.label = QLabel("QrsTweaks")
        self.label.setStyleSheet("color:#DDE1EA; font-size:11.5pt; font-weight:700;")
        layout.addWidget(self.label)
        layout.addStretch()

        # ---- Profile combo + Apply button (top-right) ----
        self.profile_combo = QComboBox()
        self.profile_combo.addItems(["Gaming Mode", "Productivity Mode", "Streaming Mode"])
        self.profile_combo.setCurrentIndex(0)  # Reset to Gaming on launch
        self.profile_combo.setFixedHeight(30)
        self.profile_combo.setStyleSheet("""
            QComboBox {
                color: #DDE1EA;
                background: rgba(255,255,255,0.08);
                border: 1px solid rgba(255,255,255,0.18);
                border-radius: 6px;
                padding: 2px 8px;
            }
            QComboBox::drop-down {
                width: 24px;
                border-left: 1px solid rgba(255,255,255,0.18);
            }
            QComboBox:hover {
                background: rgba(255,255,255,0.14);
            }
            QAbstractItemView {
                color:#DDE1EA;
                background: rgba(24,26,32,0.95);
                selection-background-color: rgba(120,200,255,0.25);
                border: 1px solid rgba(255,255,255,0.12);
            }
        """)

        self.btn_apply_profile = QPushButton("Apply Profile")
        self.btn_apply_profile.setFixedHeight(30)
        self.btn_apply_profile.setStyleSheet("""
            QPushButton {
                color:#EAF2FF;
                background: rgba(120,200,255,0.18);
                border: 1px solid rgba(120,200,255,0.35);
                border-radius: 6px;
                padding: 4px 10px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: rgba(120,200,255,0.28);
            }
        """)
        layout.addWidget(self.profile_combo)
        layout.addWidget(self.btn_apply_profile)

        # ---- Window buttons ----
        self.btn_min = QPushButton("–")
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

        # Relay profile apply from TitleBar to the window
        self.btn_apply_profile.clicked.connect(self._emit_apply_profile)

    def _emit_apply_profile(self):
        win = self.window()
        if hasattr(win, "profileApplyRequested"):
            try:
                win.profileApplyRequested.emit(self.profile_combo.currentText())
            except Exception:
                pass

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

        # Appearance controls (darkened a bit for readability)
        self._blur_alpha = 0.92
        self._base_color = QColor(20, 22, 28)

    def paintEvent(self, event):
        if not getattr(self, "_constructed", False):
            return

        painter = QPainter(self)
        if not painter.isActive():
            return
        painter.setRenderHint(QPainter.Antialiasing, True)

        # Clear
        painter.setCompositionMode(QPainter.CompositionMode_Source)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 0))

        # Rounded glass background
        painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
        path = QPainterPath()
        rect = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        path.addRoundedRect(rect, self._radius, self._radius)

        bg = QColor(self._base_color)
        bg.setAlphaF(self._blur_alpha)
        painter.fillPath(path, bg)

        # Subtle border glow
        border_color = QColor(180, 220, 255, 26)
        painter.setPen(border_color)
        painter.drawPath(path)
        painter.end()


class FramelessWindow(QWidget):
    # Emitted when user clicks "Apply Profile" (payload: profile string)
    profileApplyRequested = Signal(str)

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
