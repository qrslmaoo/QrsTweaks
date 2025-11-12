# app/pages/windows_page.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTextEdit, QLabel, QMessageBox, QScrollArea
)
from PySide6.QtCore import Qt
from app.ui.widgets.card import Card
from app.ui.widgets.toggle import Toggle
from app.ui.widgets.glow_indicator import GlowIndicator
from app.ui.animations import fade_in, slide_in_y
from src.qrs.modules.windows_optim import WindowsOptimizer


class WindowsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background: transparent;")
        self.opt = WindowsOptimizer()

        # Scrollable container
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
            }
            QScrollBar:vertical {
                background: rgba(255,255,255,0.05);
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background: rgba(255,255,255,0.2);
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background: rgba(255,255,255,0.35);
            }
        """)

        # Root content widget (inside scroll)
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(10, 10, 10, 10)
        content_layout.setSpacing(12)

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

        # =============== Actions Row 2 ===============
        row2 = QHBoxLayout()
        row2.setSpacing(12)

        leak = Card("Memory-Leak Protector")
        lv = leak.body()
        self.btn_ml_start = QPushButton("Start (Fortnite, 1024 MB)")
        self.btn_ml_stop = QPushButton("Stop")
        lv.addWidget(self.btn_ml_start)
        lv.addWidget(self.btn_ml_stop)

        net = Card("Network Optimizer")
        nv = net.body()
        self.btn_dns_cf = QPushButton("Set DNS: 1.1.1.1 / 1.0.0.1")
        self.btn_dns_gg = QPushButton("Set DNS: 8.8.8.8 / 8.8.4.4")
        self.btn_ctcp_on = QPushButton("Enable CTCP")
        self.btn_ctcp_off = QPushButton("Disable CTCP")
        self.btn_auto_norm = QPushButton("TCP Autotuning: normal")
        self.btn_auto_restr = QPushButton("TCP Autotuning: restricted")
        self.btn_nagle_off = QPushButton("Disable Nagle (gaming)")
        self.btn_ping = QPushButton("Latency test (1.1.1.1)")
        for w in (
            self.btn_dns_cf,
            self.btn_dns_gg,
            self.btn_ctcp_on,
            self.btn_ctcp_off,
            self.btn_auto_norm,
            self.btn_auto_restr,
            self.btn_nagle_off,
            self.btn_ping,
        ):
            nv.addWidget(w)

        startup = Card("Startup Optimizer")
        fv = startup.body()
        self.btn_list_startup = QPushButton("List Startup Entries")
        fv.addWidget(self.btn_list_startup)

        row2.addWidget(leak)
        row2.addWidget(net)
        row2.addWidget(startup)
        content_layout.addLayout(row2)
        content_layout.addStretch()

        # Wrap content in scroll
        scroll.setWidget(content)

        # Root layout for WindowsPage
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(scroll)

        # Connect everything
        self.btn_scan.clicked.connect(self._scan)
        self.btn_plan.clicked.connect(self._plan)
        self.btn_clean.clicked.connect(self._clean)
        self.btn_restore.clicked.connect(self._restore)
        self.btn_ml_start.clicked.connect(self._ml_start)
        self.btn_ml_stop.clicked.connect(self._ml_stop)
        self.btn_dns_cf.clicked.connect(lambda: self._dns("1.1.1.1", "1.0.0.1"))
        self.btn_dns_gg.clicked.connect(lambda: self._dns("8.8.8.8", "8.8.4.4"))
        self.btn_ctcp_on.clicked.connect(lambda: self._ctcp(True))
        self.btn_ctcp_off.clicked.connect(lambda: self._ctcp(False))
        self.btn_auto_norm.clicked.connect(lambda: self._autotune("normal"))
        self.btn_auto_restr.clicked.connect(lambda: self._autotune("restricted"))
        self.btn_nagle_off.clicked.connect(self._nagle_off)
        self.btn_ping.clicked.connect(self._ping)
        self.btn_list_startup.clicked.connect(self._startup_list)
        self.btn_clean_browsers.clicked.connect(self._deep_browsers)
        self.btn_clean_prefetch.clicked.connect(self._deep_prefetch)
        self.btn_clean_winold.clicked.connect(self._deep_winold)
        self.btn_clean_full.clicked.connect(self._deep_full)

        # Animations
        for w in (scan, power, clean, safety, deep, leak, net, startup):
            fade_in(w)
            slide_in_y(w)

    # Helper dialogs
    def _confirm(self, title, text):
        box = QMessageBox(self)
        box.setWindowTitle(title)
        box.setIcon(QMessageBox.Warning)
        box.setText(text)
        box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        return box.exec() == QMessageBox.Yes

    def _done_popup(self, title, text):
        QMessageBox.information(self, title, text)

    # Normal functions
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

    # Deep-clean handlers
    def _deep_browsers(self):
        if not self._confirm("Confirm Browser Cache Cleanup", "Delete all browser caches?"):
            return
        self.log.append("[DeepClean] Cleaning browser caches...")
        ok, msg = self.opt.cleanup_browser_caches()
        self.log.append(msg)
        self._done_popup("Deep Cleanup Complete", "Browser caches cleaned successfully.")

    def _deep_prefetch(self):
        if not self._confirm("Confirm Prefetch Cleanup", "Delete Prefetch and logs?"):
            return
        self.log.append("[DeepClean] Cleaning Prefetch & Logs...")
        ok, msg = self.opt.cleanup_prefetch_and_logs()
        self.log.append(msg)
        self._done_popup("Deep Cleanup Complete", "Prefetch and logs cleaned successfully.")

    def _deep_winold(self):
        if not self._confirm("Confirm Windows.old Removal", "PERMANENTLY delete Windows.old?"):
            return
        self.log.append("[DeepClean] Removing Windows.old...")
        ok, msg = self.opt.cleanup_windows_old()
        self.log.append(msg)
        self._done_popup("Deep Cleanup Complete", "Windows.old removed successfully.")

    def _deep_full(self):
        if not self._confirm("Confirm Full Deep Cleanup", "Run all deep cleanup actions?"):
            return
        self.log.append("[DeepClean] Running full deep cleanup...")
        ok, msg = self.opt.cleanup_deep()
        self.log.append(msg)
        self._done_popup("✅ Deep Cleanup Complete", "All cleanup operations finished successfully.")

    # Other functions remain unchanged
    def _ml_start(self):
        ok, msg = self.opt.start_memleak_protector(["FortniteClient-Win64-Shipping.exe"], 1024)
        self.log.append(msg)

    def _ml_stop(self):
        ok, msg = self.opt.stop_memleak_protector()
        self.log.append(msg)

    def _dns(self, p, s):
        ok, msg = self.opt.set_dns(p, s)
        self.log.append(msg)

    def _ctcp(self, enable):
        ok, msg = self.opt.enable_ctcp(enable)
        self.log.append(msg)

    def _autotune(self, level):
        ok, msg = self.opt.autotuning(level)
        self.log.append(msg)

    def _nagle_off(self):
        ok, msg = self.opt.toggle_nagle(False)
        self.log.append(msg)

    def _ping(self):
        ok, out = self.opt.latency_ping("1.1.1.1", 5)
        self.log.append(out)

    def _startup_list(self):
        items = self.opt.list_startup_entries()
        if not items:
            self.log.append("No startup entries found.")
            return
        self.log.append("Startup entries:")
        for loc, name, val in items:
            self.log.append(f"{name} @ {loc} -> {val}")
