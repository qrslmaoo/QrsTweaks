from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTextEdit, QLabel, QScrollArea
)
from PySide6.QtCore import Qt, QTimer
from app.ui.widgets.card import Card
    # Card/toggle/indicators unchanged
from app.ui.widgets.toggle import Toggle
from app.ui.widgets.glow_indicator import GlowIndicator
from app.ui.animations import fade_in, slide_in_y
from src.qrs.modules.windows_optim import WindowsOptimizer


class WindowsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background: transparent;")
        self.opt = WindowsOptimizer()
        self.status_indicators = {}

        # -------- Scroll container --------
        scroll = QScrollArea(self)
        scroll.setObjectName("WinPageScroll")
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # Inner widget that actually holds all content
        inner = QWidget()
        root = QVBoxLayout(inner)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(12)

        header = QLabel("Windows Optimizer")
        header.setStyleSheet("color:#DDE1EA; font-size:20pt; font-weight:700;")
        root.addWidget(header)

        # =================== Status Dashboard ===================
        status_card = Card("Optimization Status")
        status_layout = status_card.body()

        statuses = [
            "Power Plan",
            "Game Mode",
            "Visual Effects",
            "Network Optimized",
            "Memory Leak Guard",
            "Services Optimized",
        ]
        for s in statuses:
            line = QHBoxLayout()
            indicator = GlowIndicator("gray")
            indicator.setFixedSize(16, 16)
            label = QLabel(s)
            label.setStyleSheet("color:#DDE1EA; font-weight:500; font-size:10pt;")
            line.addWidget(indicator)
            line.addWidget(label)
            line.addStretch()
            status_layout.addLayout(line)
            self.status_indicators[s] = indicator

        root.addWidget(status_card)

        # =================== System Scan ===================
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
        self.log.setMinimumHeight(180)
        sv.addWidget(self.log)
        root.addWidget(scan)

        # =================== Row 1 (existing) ===================
        row1 = QHBoxLayout(); row1.setSpacing(12)

        power = Card("Power Plan"); pv = power.body()
        self.turbo = Toggle(); pv.addWidget(self.turbo)
        self.btn_plan = QPushButton("Create High Performance Plan")
        pv.addWidget(self.btn_plan)

        clean = Card("Cleanup"); cv = clean.body()
        self.btn_clean = QPushButton("Clean Temp Files")
        cv.addWidget(self.btn_clean)

        safety = Card("Safety"); sv2 = safety.body()
        self.btn_restore = QPushButton("Create Restore Point")
        sv2.addWidget(self.btn_restore)

        row1.addWidget(power); row1.addWidget(clean); row1.addWidget(safety)
        root.addLayout(row1)

        # =================== Row 2 (existing) ===================
        row2 = QHBoxLayout(); row2.setSpacing(12)

        leak = Card("Memory-Leak Protector"); lv = leak.body()
        self.btn_ml_start = QPushButton("Start (Fortnite, 1024 MB)")
        self.btn_ml_stop  = QPushButton("Stop")
        lv.addWidget(self.btn_ml_start); lv.addWidget(self.btn_ml_stop)

        net = Card("Network Optimizer"); nv = net.body()
        self.btn_dns_cf   = QPushButton("Set DNS: 1.1.1.1 / 1.0.0.1")
        self.btn_dns_gg   = QPushButton("Set DNS: 8.8.8.8 / 8.8.4.4")
        self.btn_ctcp_on  = QPushButton("Enable CTCP")
        self.btn_ctcp_off = QPushButton("Disable CTCP")
        self.btn_auto_norm = QPushButton("TCP Autotuning: normal")
        self.btn_auto_restr = QPushButton("TCP Autotuning: restricted")
        self.btn_nagle_off = QPushButton("Disable Nagle (gaming)")
        self.btn_ping = QPushButton("Latency test (1.1.1.1)")
        for w in (self.btn_dns_cf, self.btn_dns_gg, self.btn_ctcp_on, self.btn_ctcp_off,
                  self.btn_auto_norm, self.btn_auto_restr, self.btn_nagle_off, self.btn_ping):
            nv.addWidget(w)

        startup = Card("Startup Optimizer"); fv = startup.body()
        self.btn_list_startup = QPushButton("List Startup Entries")
        fv.addWidget(self.btn_list_startup)

        row2.addWidget(leak); row2.addWidget(net); row2.addWidget(startup)
        root.addLayout(row2)

        # =================== Row 3 (NEW: Task Scheduler + Storage Tools) ===================
        row3 = QHBoxLayout(); row3.setSpacing(12)

        tasks = Card("Task Scheduler Tweaks")
        tk = tasks.body()
        self.btn_tasks_list     = QPushButton("List Common Telemetry / Xbox Tasks")
        self.btn_tasks_disable  = QPushButton("Disable Telemetry Tasks")
        self.btn_tasks_enable   = QPushButton("Enable Telemetry Tasks")
        self.btn_xbox_disable   = QPushButton("Disable Xbox Tasks")
        self.btn_xbox_enable    = QPushButton("Enable Xbox Tasks")
        for b in (self.btn_tasks_list, self.btn_tasks_disable, self.btn_tasks_enable,
                  self.btn_xbox_disable, self.btn_xbox_enable):
            tk.addWidget(b)

        storage = Card("Storage Tools")
        st = storage.body()
        self.btn_storage_analyze  = QPushButton("Analyze Disk Usage")
        self.btn_storage_winsxs   = QPushButton("Compact WinSxS (DISM)")
        self.btn_storage_prefetch = QPushButton("Purge Prefetch Cache")
        self.btn_storage_old      = QPushButton("Remove Windows.old (if present)")
        for b in (self.btn_storage_analyze, self.btn_storage_winsxs,
                  self.btn_storage_prefetch, self.btn_storage_old):
            st.addWidget(b)

        row3.addWidget(tasks)
        row3.addWidget(storage)
        root.addLayout(row3)

        # =================== Row 4 (Restore Defaults & Logs) ===================
        row4 = QHBoxLayout(); row4.setSpacing(12)

        restore = Card("Restore Defaults & Logs")
        rs = restore.body()
        self.btn_restore_defaults = QPushButton("Restore Defaults (Revert Common Tweaks)")
        self.btn_logs_export      = QPushButton("Export Logs (zip)")
        self.btn_logs_open        = QPushButton("Open Logs Folder")
        rs.addWidget(self.btn_restore_defaults)
        rs.addWidget(self.btn_logs_export)
        rs.addWidget(self.btn_logs_open)

        row4.addWidget(restore)
        root.addLayout(row4)

        # Finish inner setup and mount into scroll area
        root.addStretch()
        scroll.setWidget(inner)

        # This page's layout holds just the scroll area
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

        # =================== Signals (existing basics) ===================
        self.btn_scan.clicked.connect(self._scan)
        self.btn_plan.clicked.connect(self._plan)
        self.btn_clean.clicked.connect(self._clean)
        self.btn_restore.clicked.connect(self._restore)

        self.btn_ml_start.clicked.connect(self._ml_start)
        self.btn_ml_stop.clicked.connect(self._ml_stop)

        self.btn_dns_cf.clicked.connect(lambda: self._call(self.opt.set_dns, "DNS", "1.1.1.1", "1.0.0.1"))
        self.btn_dns_gg.clicked.connect(lambda: self._call(self.opt.set_dns, "DNS", "8.8.8.8", "8.8.4.4"))
        self.btn_ctcp_on.clicked.connect(lambda: self._call(self.opt.enable_ctcp, "CTCP", True))
        self.btn_ctcp_off.clicked.connect(lambda: self._call(self.opt.enable_ctcp, "CTCP", False))
        self.btn_auto_norm.clicked.connect(lambda: self._call(self.opt.autotuning, "TCP", "normal"))
        self.btn_auto_restr.clicked.connect(lambda: self._call(self.opt.autotuning, "TCP", "restricted"))
        self.btn_nagle_off.clicked.connect(lambda: self._call(self.opt.toggle_nagle, "Nagle", True))
        self.btn_ping.clicked.connect(lambda: self._ping())
        self.btn_list_startup.clicked.connect(self._startup_list)

        # NEW: Task Scheduler + Storage + Restore Defaults + Logs
        self.btn_tasks_list.clicked.connect(lambda: self._call(self.opt.list_common_tasks, "Tasks"))
        self.btn_tasks_disable.clicked.connect(lambda: self._call(self.opt.disable_telemetry_tasks, "Tasks"))
        self.btn_tasks_enable.clicked.connect(lambda: self._call(self.opt.enable_telemetry_tasks, "Tasks"))
        self.btn_xbox_disable.clicked.connect(lambda: self._call(self.opt.disable_xbox_tasks, "Tasks"))
        self.btn_xbox_enable.clicked.connect(lambda: self._call(self.opt.enable_xbox_tasks, "Tasks"))

        self.btn_storage_analyze.clicked.connect(lambda: self._call(self.opt.analyze_disk_usage, "Storage"))
        self.btn_storage_winsxs.clicked.connect(lambda: self._call(self.opt.compact_winsxs, "Storage"))
        self.btn_storage_prefetch.clicked.connect(lambda: self._call(self.opt.purge_prefetch_cache, "Storage"))
        self.btn_storage_old.clicked.connect(lambda: self._call(self.opt.remove_windows_old, "Storage"))

        self.btn_restore_defaults.clicked.connect(lambda: self._call(self.opt.restore_defaults, "Restore"))
        self.btn_logs_export.clicked.connect(lambda: self._call(self.opt.export_logs_zip, "Logs"))
        self.btn_logs_open.clicked.connect(lambda: self._call(self.opt.open_logs_folder, "Logs"))

        # Animations
        for w in (status_card, scan, power, clean, safety, leak, net, startup,
                  tasks, storage, restore):
            fade_in(w); slide_in_y(w)

        # Initial status refresh
        self._refresh_status()
        self._status_timer = QTimer(self)
        self._status_timer.timeout.connect(self._refresh_status)
        self._status_timer.start(10000)

    # =================== Helpers / Logic ===================
    def _log(self, tag, msg):
        self.log.append(f"[{tag}] {msg}")

    def _call(self, fn, tag, *args):
        try:
            ok, msg = fn(*args)
            self._log(tag, msg)
        except Exception as e:
            ok, msg = False, str(e)
            self._log(tag, f"Error: {msg}")
        self._refresh_status()

    def _scan(self):
        self.spinner.show()
        self.log.clear()
        self.log.append(self.opt.quick_scan())
        self.spinner.hide()

    def _plan(self):
        ok, msg = self.opt.create_high_perf_powerplan()
        self._log("Power", msg)
        self._refresh_status()

    def _clean(self):
        n = self.opt.cleanup_temp_files()
        self._log("Cleanup", f"Removed ~{n} temp files.")

    def _restore(self):
        ok, msg = self.opt.create_restore_point("QrsTweaks Snapshot")
        self._log("Restore", msg)

    def _refresh_status(self):
        checks = [
            ("Power Plan", self.opt.is_high_perf_plan),
            ("Game Mode", self.opt.is_game_mode_enabled),
            ("Visual Effects", self.opt.is_visual_effects_minimized),
            ("Network Optimized", self.opt.is_network_optimized),
            ("Memory Leak Guard", self.opt.is_memleak_guard_active),
            ("Services Optimized", self.opt.is_services_optimized),
        ]
        for label, func in checks:
            indicator = self.status_indicators[label]
            active = False
            try:
                active = func()
            except Exception:
                active = False
            indicator.setColor("lime" if active else "gray")

    # --- Memory leak guard (placeholder hooks) ---
    def _ml_start(self):
        ok, msg = self.opt.start_memleak_protector(
            process_names=["FortniteClient-Win64-Shipping.exe"], mb_threshold=1024
        )
        self._log("MemLeak", msg); self._refresh_status()

    def _ml_stop(self):
        ok, msg = self.opt.stop_memleak_protector()
        self._log("MemLeak", msg); self._refresh_status()

    # --- Network ---
    def _ping(self):
        ok, out = self.opt.latency_ping("1.1.1.1", 5)
        self._log("Ping", out if ok else f"Error: {out}")

    # --- Startup ---
    def _startup_list(self):
        items = self.opt.list_startup_entries()
        if not items:
            self._log("Startup", "No entries found."); return
        self._log("Startup", "Entries:")
        for loc, name, val in items:
            self._log("Startup", f"  - {name} @ {loc} => {val}")
