from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTextEdit, QLabel, QFrame
)
from PySide6.QtGui import QColor
from src.qrs.modules.windows_optim import WindowsOptimizer
from app.ui.widgets.card import Card
from app.ui.widgets.toggle import Toggle
from app.ui.widgets.glow_indicator import GlowIndicator
from app.ui.animations import fade_in, slide_in_y

class Chip(QLabel):
    def __init__(self, text, kind="ok", parent=None):
        super().__init__(text, parent)
        self.setProperty("class", "StatChip")
        if kind == "ok": self.setProperty("ok", True)
        if kind == "warn": self.setProperty("warn", True)
        if kind == "danger": self.setProperty("danger", True)
        self.setStyleSheet("")  # re-polish

class WindowsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.opt = WindowsOptimizer()

        root = QVBoxLayout(self); root.setContentsMargins(6,6,6,6); root.setSpacing(10)

        # Header / hero
        header = QLabel("Windows Optimization")
        header.setStyleSheet("color:#DDE1EA; font-size:20pt; font-weight:700;")
        root.addWidget(header)

        # Status chips row
        rowchips = QHBoxLayout(); rowchips.setSpacing(8)
        self.chip_os = Chip("OS: —", "ok")
        self.chip_free = Chip("Free: —", "warn")
        self.chip_temp = Chip("Temp: —", "danger")
        for c in (self.chip_os, self.chip_free, self.chip_temp):
            w = QFrame(); w.setLayout(QHBoxLayout()); w.layout().setContentsMargins(10,6,10,6); w.setProperty("class","StatChip"); w.layout().addWidget(c)
            rowchips.addWidget(w)
        root.addLayout(rowchips)

        # Scan card
        scan = Card("System Scan"); scan.setObjectName("Card")
        sv = scan.body()
        top = QHBoxLayout()
        self.btn_scan = QPushButton("Run Quick Scan")
        self.spinner = GlowIndicator(); self.spinner.hide()
        top.addWidget(self.btn_scan); top.addStretch(); top.addWidget(self.spinner)
        sv.addLayout(top)

        self.log = QTextEdit(); self.log.setReadOnly(True)
        self.log.setFixedHeight(260)
        self.log.setProperty("class", "Neon")
        sv.addWidget(self.log)

        # Action row (three cards)
        row = QHBoxLayout(); row.setSpacing(14)

        power = Card("Power Plan"); pv = power.body()
        self.turbo = Toggle()
        bpower = QPushButton("Create High Performance plan")
        pv.addWidget(self.turbo); pv.addWidget(bpower)

        clean = Card("Cleanup"); cv = clean.body()
        bclean = QPushButton("Clean Temp Files")
        cv.addWidget(bclean)

        restore = Card("Safety"); rv = restore.body()
        bres = QPushButton("Create Restore Point")
        rv.addWidget(bres)

        row.addWidget(power); row.addWidget(clean); row.addWidget(restore)
        root.addWidget(scan); root.addLayout(row); root.addStretch()

        # Wire
        self.btn_scan.clicked.connect(self._scan)
        bpower.clicked.connect(self._power)
        bclean.clicked.connect(self._clean)
        bres.clicked.connect(self._restore)

        # gentle entrance
        fade_in(scan); slide_in_y(scan); slide_in_y(power); slide_in_y(clean); slide_in_y(restore)

    def _scan(self):
        self.spinner.show()
        self.log.clear()
        report = self.opt.quick_scan()
        self.log.setPlainText(report)
        # update chips from report lines
        lines = {k.strip(): v.strip() for k,v in (l.split(":",1) for l in report.splitlines() if ":" in l)}
        self.chip_os.setText(f"OS: {lines.get('OS','—')}")
        self.chip_free.setText(f"Free: {lines.get('System drive free','—')}")
        # crude temp risk
        try:
            temp_line = [l for l in report.splitlines() if l.lower().startswith("temp files")][0]
            count = int(''.join(ch for ch in temp_line if ch.isdigit()))
            self.chip_temp.setText(f"Temp: {count}")
        except Exception:
            pass
        self.spinner.hide()

    def _power(self):
        ok, msg = self.opt.create_high_perf_powerplan()
        self.log.append(f"[Power] {msg}")

    def _clean(self):
        n = self.opt.cleanup_temp_files()
        self.log.append(f"[Cleanup] Removed ~{n} temp files.")

    def _restore(self):
        ok, msg = self.opt.create_restore_point("QrsTweaks Snapshot")
        self.log.append(f"[Restore] {msg if ok else 'Failed: ' + msg}")
