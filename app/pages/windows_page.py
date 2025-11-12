# app/pages/windows_page.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTextEdit, QLabel, QScrollArea
)
from PySide6.QtCore import Qt, QThread, Signal
from app.ui.widgets.card import Card
from app.ui.widgets.toggle import Toggle
from app.ui.widgets.glow_indicator import GlowIndicator
from app.ui.animations import fade_in, slide_in_y
from src.qrs.modules.windows_optim import WindowsOptimizer


# ---------- Thread worker for long scans ----------
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
            QScrollBar::handle:vertical { background: rgba(255,255,255,0.20); border-radius: 6px; min-height: 20px; }
            QScrollBar::handle:vertical:hover { background: rgba(255,255,255,0.35); }
        """)

        content = QWidget()
        root = QVBoxLayout(content)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(12)

        # Header
        header = QLabel("Windows Optimizer")
        header.setStyleSheet("color:#DDE1EA; font-size:20pt; font-weight:700;")
        root.addWidget(header)

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
        root.addWidget(scan)

        # =============== Actions Row 1 ===============
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
        root.addLayout(row1)

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
        root.addWidget(deep)

        # =============== Divider: Storage Tools ===============
        divider_storage = QLabel("──────────────  Storage Tools  ───────────────")
        divider_storage.setAlignment(Qt.AlignHCenter)
        divider_storage.setStyleSheet("""
            color: rgba(210,220,245,0.9);
            font-size: 11pt; font-weight: 600; letter-spacing: 0.5px;
            padding: 10px 0;
        """)
        root.addWidget(divider_storage)

        # =============== Storage Tools ===============
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
        root.addLayout(storage_row)

        # =============== Divider: System Optimization ===============
        divider_system = QLabel("──────────────  System Optimization  ───────────────")
        divider_system.setAlignment(Qt.AlignHCenter)
        divider_system.setStyleSheet("""
            color: rgba(210,220,245,0.9);
            font-size: 11pt; font-weight: 600; letter-spacing: 0.5px;
            padding: 10px 0;
        """)
        root.addWidget(divider_system)

        # =============== System Optimization ===============
        sys_row = QHBoxLayout()
        sys_row.setSpacing(12)

        perf_card = Card("Performance & Service Tweaks")
        pv2 = perf_card.body()
        self.btn_apply_tweaks = QPushButton("Apply Recommended System Tweaks")
        self.btn_revert_tweaks = QPushButton("Revert to Default Windows Settings")
        pv2.addWidget(self.btn_apply_tweaks)
        pv2.addWidget(self.btn_revert_tweaks)

        game_card = Card("Gaming Mode Enhancer")
        gv = game_card.body()
        self.btn_apply_gaming = QPushButton("Apply Gaming Mode")
        self.btn_revert_gaming = QPushButton("Revert to Normal Mode")
        gv.addWidget(self.btn_apply_gaming)
        gv.addWidget(self.btn_revert_gaming)

        sys_row.addWidget(perf_card)
        sys_row.addWidget(game_card)
        root.addLayout(sys_row)

        # ====================================================
        # 🧩 Startup & Background Services
        # ====================================================
        divider_startup = QLabel("──────────────  Startup & Background Services  ───────────────")
        divider_startup.setAlignment(Qt.AlignHCenter)
        divider_startup.setStyleSheet("""
            color: rgba(210,220,245,0.9);
            font-size: 11pt; font-weight: 600; letter-spacing: 0.5px;
            padding: 14px 0;
        """)
        root.addWidget(divider_startup)

        startup_row = QHBoxLayout()
        startup_row.setSpacing(12)

        startup_card = Card("Startup Apps Manager")
        sm = startup_card.body()
        self.btn_list_startup = QPushButton("List All Startup Apps")
        self.btn_disable_startup = QPushButton("Disable Selected Apps")
        self.btn_enable_startup = QPushButton("Enable Selected Apps")
        self.btn_remove_startup = QPushButton("Remove Entry")
        for w in (
            self.btn_list_startup,
            self.btn_disable_startup,
            self.btn_enable_startup,
            self.btn_remove_startup,
        ):
            sm.addWidget(w)

        bg_card = Card("Background Service Optimizer")
        bm = bg_card.body()
        self.btn_list_heavy = QPushButton("Show Heavy Background Services")
        self.btn_disable_non = QPushButton("Disable Non-Essential Services")
        self.btn_restore_serv = QPushButton("Restore Default Services")
        bm.addWidget(self.btn_list_heavy)
        bm.addWidget(self.btn_disable_non)
        bm.addWidget(self.btn_restore_serv)

        startup_row.addWidget(startup_card)
        startup_row.addWidget(bg_card)
        root.addLayout(startup_row)

        # Stretch and finalize
        root.addStretch()
        scroll.setWidget(content)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(scroll)

        # ---- Signals ----
        self.btn_scan.clicked.connect(self._scan)
        self.btn_plan.clicked.connect(self._plan)
        self.btn_clean.clicked.connect(self._clean)
        self.btn_restore.clicked.connect(self._restore)

        self.btn_clean_browsers.clicked.connect(self._deep_browsers)
        self.btn_clean_prefetch.clicked.connect(self._deep_prefetch)
        self.btn_clean_winold.clicked.connect(self._deep_winold)
        self.btn_clean_full.clicked.connect(self._deep_full)

        self.btn_analyze_files.clicked.connect(self._analyze_files_threaded)
        self.btn_analyze_dirs.clicked.connect(self._analyze_dirs_threaded)
        self.btn_ssd_trim.clicked.connect(self._ssd_trim)
        self.btn_hdd_defrag.clicked.connect(self._hdd_defrag)
        self.btn_winupdate.clicked.connect(self._winupdate_cleanup)
        self.btn_drive_health.clicked.connect(self._drive_health)

        self.btn_apply_tweaks.clicked.connect(self._apply_tweaks)
        self.btn_revert_tweaks.clicked.connect(self._revert_tweaks)
        self.btn_apply_gaming.clicked.connect(self._apply_gaming)
        self.btn_revert_gaming.clicked.connect(self._revert_gaming)

        self.btn_list_startup.clicked.connect(self._startup_list)
        self.btn_disable_startup.clicked.connect(self._startup_disable_auto)
        self.btn_enable_startup.clicked.connect(self._startup_enable_disabled)
        self.btn_remove_startup.clicked.connect(self._startup_remove_disabled)

        self.btn_list_heavy.clicked.connect(self._services_list_heavy)
        self.btn_disable_non.clicked.connect(self._services_disable_non)
        self.btn_restore_serv.clicked.connect(self._services_restore_defaults)

        # ---- Animations ----
        for w in (
            scan, power, clean, safety, deep, disk_an, storage_opt, drive_health,
            perf_card, game_card, startup_card, bg_card
        ):
            fade_in(w)
            slide_in_y(w)

    # ---------- Core ----------
    def _scan(self):
        self.spinner.show()
        self.log.clear()
        self.log.append(self.opt.quick_scan())
        self.spinner.hide()

    def _plan(self):
        ok, msg = self.opt.create_high_perf_powerplan()
        self.log.append(f"[Power] {msg}")

    def _clean(self):
        n = self.opt.cleanup_temp_files()
        self.log.append(f"[Cleanup] Removed ~{n} temp files.")

    def _restore(self):
        ok, msg = self.opt.create_restore_point("QrsTweaks Snapshot")
        self.log.append(f"[Restore] {msg}")

    # ---------- Deep cleanup ----------
    def _deep_browsers(self):
        ok, msg = self.opt.cleanup_browser_caches()
        self.log.append(f"[DeepClean] {msg}")

    def _deep_prefetch(self):
        ok, msg = self.opt.cleanup_prefetch_and_logs()
        self.log.append(f"[DeepClean] {msg}")

    def _deep_winold(self):
        ok, msg = self.opt.cleanup_windows_old()
        self.log.append(f"[DeepClean] {msg}")

    def _deep_full(self):
        ok, msg = self.opt.cleanup_deep()
        self.log.append(f"[DeepClean]\n{msg}")

    # ---------- Storage (threaded) ----------
    def _analyze_files_threaded(self):
        self.btn_analyze_files.setEnabled(False)
        self.log.append("[Storage] Analyzing largest files...")
        t = _ScanThread(self.opt.analyze_largest_files, limit=25)
        t.finished_text.connect(lambda text: self.log.append(text))
        t.failed_text.connect(lambda text: self.log.append("[Storage] File analysis failed:\n" + text))
        t.finished.connect(lambda: self.btn_analyze_files.setEnabled(True))
        t.finished.connect(lambda: self._threads.remove(t) if t in self._threads else None)
        self._threads.append(t)
        t.start()

    def _analyze_dirs_threaded(self):
        self.btn_analyze_dirs.setEnabled(False)
        self.log.append("[Storage] Analyzing top directories...")
        t = _ScanThread(self.opt.analyze_top_dirs, limit=10)
        t.finished_text.connect(lambda text: self.log.append(text))
        t.failed_text.connect(lambda text: self.log.append("[Storage] Directory analysis failed:\n" + text))
        t.finished.connect(lambda: self.btn_analyze_dirs.setEnabled(True))
        t.finished.connect(lambda: self._threads.remove(t) if t in self._threads else None)
        self._threads.append(t)
        t.start()

    # ---------- Storage (sync) ----------
    def _ssd_trim(self):
        ok, msg = self.opt.optimize_ssd_trim()
        self.log.append(f"[Storage] {msg}")

    def _hdd_defrag(self):
        ok, msg = self.opt.optimize_hdd_defrag()
        self.log.append(f"[Storage] {msg}")

    def _winupdate_cleanup(self):
        ok, msg = self.opt.cleanup_windows_updates()
        self.log.append(f"[Storage] {msg}")

    def _drive_health(self):
        ok, msg = self.opt.check_drive_health()
        self.log.append(msg)

    # ---------- System Optimization ----------
    def _apply_tweaks(self):
        ok, msg = self.opt.apply_system_tweaks()
        self.log.append("[SystemTweaks] " + msg)

    def _revert_tweaks(self):
        ok, msg = self.opt.revert_system_defaults()
        self.log.append("[SystemTweaks] " + msg)

    def _apply_gaming(self):
        ok, msg = self.opt.apply_gaming_mode()
        self.log.append("[GamingMode] " + msg)

    def _revert_gaming(self):
        ok, msg = self.opt.revert_normal_mode()
        self.log.append("[GamingMode] " + msg)

    # ---------- Startup Apps ----------
    def _startup_list(self):
        ok, msg = self.opt.list_startup_entries_detailed()
        self.log.append(msg)

    def _startup_disable_auto(self):
        ok, msg = self.opt.disable_startup_auto()
        self.log.append("[Startup] " + msg)

    def _startup_enable_disabled(self):
        ok, msg = self.opt.enable_startup_disabled()
        self.log.append("[Startup] " + msg)

    def _startup_remove_disabled(self):
        ok, msg = self.opt.remove_startup_disabled()
        self.log.append("[Startup] " + msg)

    # ---------- Background Services ----------
    def _services_list_heavy(self):
        ok, msg = self.opt.list_heavy_services()
        self.log.append(msg)

    def _services_disable_non(self):
        ok, msg = self.opt.disable_non_essential_services()
        self.log.append("[Service] " + msg)

    def _services_restore_defaults(self):
        ok, msg = self.opt.restore_default_services()
        self.log.append("[Service] " + msg)
