# app/pages/windows_page.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTextEdit, QLabel, QMessageBox, QScrollArea
)
from PySide6.QtCore import Qt, QThread, Signal
from app.ui.widgets.card import Card
from app.ui.widgets.toggle import Toggle
from app.ui.widgets.glow_indicator import GlowIndicator
from app.ui.animations import fade_in, slide_in_y
from src.qrs.modules.windows_optim import WindowsOptimizer


class _ScanThread(QThread):
    finished_text = Signal(str)
    failed_text = Signal(str)

    def __init__(self, fn, *args, **kwargs):
        super().__init__()
        self._fn = fn
        self._args = args
        self._kwargs = kwargs

    def run(self):
        try:
            ok, msg = self._fn(*self._args, **self._kwargs)
            if ok:
                self.finished_text.emit(msg or "")
            else:
                self.failed_text.emit(msg or "Unknown error")
        except Exception as e:
            self.failed_text.emit(str(e))


class WindowsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background: transparent;")
        self.opt = WindowsOptimizer()
        self._threads = []

        # ---------- Scroll container ----------
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("""
            QScrollArea { border: none; background: transparent; }
            QScrollBar:vertical { background: rgba(255,255,255,0.05); width: 12px; border-radius: 6px; }
            QScrollBar::handle:vertical { background: rgba(255,255,255,0.2); border-radius: 6px; min-height: 20px; }
            QScrollBar::handle:vertical:hover { background: rgba(255,255,255,0.35); }
        """)

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(10, 10, 10, 10)
        content_layout.setSpacing(12)

        # Header
        header = QLabel("Windows Optimizer")
        header.setStyleSheet("color:#DDE1EA; font-size:20pt; font-weight:700;")
        content_layout.addWidget(header)

        # =============== System Scan ===============
        scan = Card("System Scan")
        sv = scan.body()
        top = QHBoxLayout()
        self.btn_scan = QPushButton("Run Quick Scan")
        self.spinner = GlowIndicator()
        self.spinner.hide()
        top.addWidget(self.btn_scan)
        top.addStretch()
        top.addWidget(self.spinner)
        sv.addLayout(top)

        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setMinimumHeight(220)
        sv.addWidget(self.log)
        content_layout.addWidget(scan)

        # =============== Row 1 (Power / Clean / Safety) ===============
        row1 = QHBoxLayout()
        row1.setSpacing(12)

        power = Card("Power Plan")
        pv = power.body()
        self.turbo = Toggle()
        pv.addWidget(self.turbo)
        self.btn_plan = QPushButton("Create High Performance Plan")
        pv.addWidget(self.btn_plan)

        clean = Card("Cleanup")
        cv = clean.body()
        self.btn_clean = QPushButton("Clean Temp Files (Quick)")
        cv.addWidget(self.btn_clean)

        safety = Card("Safety")
        sv2 = safety.body()
        self.btn_restore = QPushButton("Create Restore Point")
        sv2.addWidget(self.btn_restore)

        row1.addWidget(power)
        row1.addWidget(clean)
        row1.addWidget(safety)
        content_layout.addLayout(row1)

        # =============== Deep Cleanup ===============
        deep = Card("Deep Cleanup")
        dv = deep.body()
        self.btn_clean_browsers = QPushButton("Clean Browser Caches (Chrome/Edge/Brave/Firefox)")
        self.btn_clean_prefetch = QPushButton("Clean Prefetch & System Logs")
        self.btn_clean_winold = QPushButton("Remove Windows.old (Permanent)")
        self.btn_clean_full = QPushButton("Run Full Deep Cleanup")
        for b in (
            self.btn_clean_browsers,
            self.btn_clean_prefetch,
            self.btn_clean_winold,
            self.btn_clean_full,
        ):
            dv.addWidget(b)
        content_layout.addWidget(deep)

        # =============== Divider: Storage Tools ===============
        divider_storage = QLabel("──────────────  Storage Tools  ───────────────")
        divider_storage.setAlignment(Qt.AlignHCenter)
        divider_storage.setStyleSheet("""
            color: rgba(210,220,245,0.9);
            font-size: 11pt; font-weight: 600; letter-spacing: 0.5px;
            padding: 10px 0;
        """)
        content_layout.addWidget(divider_storage)

        # =============== Storage Tools Row ===============
        storage_row = QHBoxLayout()
        storage_row.setSpacing(12)

        disk_an = Card("Disk Analyzer")
        dav = disk_an.body()
        self.btn_analyze_files = QPushButton("Analyze Largest Files (Top 25)")
        self.btn_analyze_dirs = QPushButton("Show Top Directories (by size)")
        dav.addWidget(self.btn_analyze_files)
        dav.addWidget(self.btn_analyze_dirs)

        storage_opt = Card("Storage Optimizer")
        sov = storage_opt.body()
        self.btn_ssd_trim = QPushButton("Optimize SSD (TRIM)")
        self.btn_hdd_defrag = QPushButton("Defrag HDD (Safe)")
        self.btn_winupdate = QPushButton("Clean Windows Update Files")
        sov.addWidget(self.btn_ssd_trim)
        sov.addWidget(self.btn_hdd_defrag)
        sov.addWidget(self.btn_winupdate)

        drive_health = Card("Drive Health")
        dhv = drive_health.body()
        self.btn_drive_health = QPushButton("Check Drive Health")
        dhv.addWidget(self.btn_drive_health)

        storage_row.addWidget(disk_an)
        storage_row.addWidget(storage_opt)
        storage_row.addWidget(drive_health)
        content_layout.addLayout(storage_row)

        # =============== Divider: System Optimization ===============
        divider_system = QLabel("──────────────  System Optimization  ───────────────")
        divider_system.setAlignment(Qt.AlignHCenter)
        divider_system.setStyleSheet("""
            color: rgba(210,220,245,0.9);
            font-size: 11pt; font-weight: 600; letter-spacing: 0.5px;
            padding: 10px 0;
        """)
        content_layout.addWidget(divider_system)

        # =============== System Optimization Cards ===============
        sys_row = QHBoxLayout()
        sys_row.setSpacing(12)

        # Performance Tweaks Card
        perf_card = Card("Performance & Service Tweaks")
        pv2 = perf_card.body()
        self.btn_apply_tweaks = QPushButton("Apply Recommended System Tweaks")
        self.btn_revert_tweaks = QPushButton("Revert to Default Windows Settings")
        pv2.addWidget(self.btn_apply_tweaks)
        pv2.addWidget(self.btn_revert_tweaks)

        # Gaming Mode Card
        game_card = Card("Gaming Mode Enhancer")
        gv = game_card.body()
        self.btn_apply_gaming = QPushButton("Apply Gaming Mode")
        self.btn_revert_gaming = QPushButton("Revert to Normal Mode")
        gv.addWidget(self.btn_apply_gaming)
        gv.addWidget(self.btn_revert_gaming)

        sys_row.addWidget(perf_card)
        sys_row.addWidget(game_card)
        content_layout.addLayout(sys_row)

        # Stretch for bottom padding
        content_layout.addStretch()
        scroll.setWidget(content)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(scroll)

        # Animations
        for w in (
            scan,
            power,
            clean,
            safety,
            deep,
            disk_an,
            storage_opt,
            drive_health,
            perf_card,
            game_card,
        ):
            fade_in(w)
            slide_in_y(w)
