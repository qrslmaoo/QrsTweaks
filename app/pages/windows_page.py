# app/pages/windows_page.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTextEdit, QLabel
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

        self.opt = WindowsOptimizer()

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(18)

        # ---------------- Header ----------------
        header = QLabel("Windows Optimizer")
        header.setStyleSheet("color:#DDE1EA; font-size:22pt; font-weight:700;")
        header.setAlignment(Qt.AlignLeft)
        root.addWidget(header)

        # =======================================================
        #                     SYSTEM SCAN CARD
        # =======================================================
        scan = Card("System Scan")
        body = scan.body()

        # Top row (Button + spinner)
        row = QHBoxLayout()
        self.btn_scan = QPushButton("Run Quick Scan")
        self.spinner = GlowIndicator()
        self.spinner.hide()

        row.addWidget(self.btn_scan)
        row.addStretch()
        row.addWidget(self.spinner)

        body.addLayout(row)

        # Log window
        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setMinimumHeight(230)
        body.addWidget(self.log)

        root.addWidget(scan)

        # =======================================================
        #                       ROW 1
        # =======================================================
        row1 = QHBoxLayout()
        row1.setSpacing(18)

        # ----- Power Plan -----
        power = Card("Power Plan")
        pv = power.body()

        self.turbo = Toggle()
        self.btn_plan = QPushButton("Create High Performance Plan")

        pv.addWidget(self.turbo)
        pv.addWidget(self.btn_plan)

        # ----- Cleanup -----
        clean = Card("Cleanup")
        cv = clean.body()

        self.btn_clean = QPushButton("Clean Temp Files")
        cv.addWidget(self.btn_clean)

        # ----- Safety -----
        safety = Card("Safety")
        sv = safety.body()

        self.btn_restore = QPushButton("Create Restore Point")
        sv.addWidget(self.btn_restore)

        row1.addWidget(power)
        row1.addWidget(clean)
        row1.addWidget(safety)
        root.addLayout(row1)

        # =======================================================
        #                       ROW 2
        # =======================================================
        row2 = QHBoxLayout()
        row2.setSpacing(18)

        # ----- Memory Leak Protector -----
        leak = Card("Memory-Leak Protector")
        lv = leak.body()

        self.btn_ml_start = QPushButton("Start (Fortnite, 1024 MB)")
        self.btn_ml_stop = QPushButton("Stop")

        lv.addWidget(self.btn_ml_start)
        lv.addWidget(self.btn_ml_stop)

        # ----- Network Optimizer -----
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
            self.btn_dns_cf, self.btn_dns_gg,
            self.btn_ctcp_on, self.btn_ctcp_off,
            self.btn_auto_norm, self.btn_auto_restr,
            self.btn_nagle_off, self.btn_ping
        ):
            nv.addWidget(w)

        # ----- Startup Optimizer -----
        startup = Card("Startup Optimizer")
        st = startup.body()

        self.btn_list_startup = QPushButton("List Startup Entries")
        st.addWidget(self.btn_list_startup)

        row2.addWidget(leak)
        row2.addWidget(net)
        row2.addWidget(startup)
        root.addLayout(row2)

        # Stretch bottom
        root.addStretch()

        # ================= SIGNALS ==================
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

        # ================= ANIMATIONS ==================
        for card in (scan, power, clean, safety, leak, net, startup):
            fade_in(card)
            slide_in_y(card)

    # ================= LOGIC ==================
    def _scan(self):
        self.spinner.show()
        self.log.clear()
        self.log.append(self.opt.quick_scan())
        self.spinner.hide()

    def _plan(self):
        ok, msg = self.opt.create_high_perf_powerplan()
        self.log.append(f"[Power] {msg}")

    def _clean(self):
        removed = self.opt.cleanup_temp_files()
        self.log.append(f"[Cleanup] Removed ~{removed} temp files.")

    def _restore(self):
        ok, msg = self.opt.create_restore_point("QrsTweaks Snapshot")
        self.log.append(f"[Restore] {msg}")

    # Memory Leak Protector
    def _ml_start(self):
        ok, msg = self.opt.start_memleak_protector(
            process_names=["FortniteClient-Win64-Shipping.exe"],
            mb_threshold=1024
        )
        self.log.append(f"[MemLeak] {msg}")

    def _ml_stop(self):
        ok, msg = self.opt.stop_memleak_protector()
        self.log.append(f"[MemLeak] {msg}")

    # Network Optimizer
    def _dns(self, a, b):
        ok, msg = self.opt.set_dns(primary=a, secondary=b)
        self.log.append(f"[DNS] {msg}")

    def _ctcp(self, enable):
        ok, msg = self.opt.enable_ctcp(enable)
        self.log.append(f"[CTCP] {msg}")

    def _autotune(self, mode):
        ok, msg = self.opt.autotuning(mode)
        self.log.append(f"[TCP] {msg}")

    def _nagle_off(self):
        ok, msg = self.opt.toggle_nagle(False)
        self.log.append(f"[Nagle] {msg}")

    def _ping(self):
        ok, out = self.opt.latency_ping("1.1.1.1", 5)
        self.log.append(out)

    # Startup
    def _startup_list(self):
        entries = self.opt.list_startup_entries()
        if not entries:
            self.log.append("[Startup] No items found.")
            return
        self.log.append("[Startup]")
        for loc, name, val in entries:
            self.log.append(f"  - {name} @ {loc} => {val}")
