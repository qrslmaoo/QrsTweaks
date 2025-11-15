# app/pages/windows_page.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTextEdit, QLabel, QScrollArea, QFileDialog
)
from PySide6.QtCore import Qt

from app.ui.widgets.card import Card
from app.ui.widgets.toggle import Toggle
from app.ui.widgets.glow_indicator import GlowIndicator
from app.ui.widgets.divider import Divider

from src.qrs.modules.windows_optim import WindowsOptimizer


class WindowsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background: transparent;")

        # backend
        self.opt = WindowsOptimizer()

        # SCROLL WRAPPER
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setFrameShape(QScrollArea.NoFrame)
        scroll.setStyleSheet("background: transparent;")

        container = QWidget()
        scroll.setWidget(container)

        root = QVBoxLayout(container)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(16)

        # TITLE
        title = QLabel("Windows Optimizer")
        title.setStyleSheet("font-size: 22pt; color: #DDE1EA; font-weight:700;")
        root.addWidget(title)

        # SYSTEM SCAN
        scan = Card("System Scan")
        v = scan.body()

        head = QHBoxLayout()
        self.btn_scan = QPushButton("Run Quick Scan")
        self.spinner = GlowIndicator()
        self.spinner.hide()

        head.addWidget(self.btn_scan)
        head.addStretch()
        head.addWidget(self.spinner)
        v.addLayout(head)

        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setMinimumHeight(200)
        v.addWidget(self.log)

        root.addWidget(scan)

        # ROW 1 ----------------------------------
        row1 = QHBoxLayout()
        row1.setSpacing(12)

        # POWER PLAN
        power = Card("Power Plan")
        pv = power.body()
        self.turbo = Toggle()
        pv.addWidget(self.turbo)
        self.btn_plan = QPushButton("Create High Performance Plan")
        pv.addWidget(self.btn_plan)

        # CLEANUP
        cleanup = Card("Cleanup")
        cl = cleanup.body()
        self.btn_clean = QPushButton("Clean Temp Files")
        self.btn_deep_clean = QPushButton("Deep Cleanup (System/Junk)")
        cl.addWidget(self.btn_clean)
        cl.addWidget(self.btn_deep_clean)

        # SAFETY
        safety = Card("Safety")
        st = safety.body()
        self.btn_restore = QPushButton("Create Restore Point")
        st.addWidget(self.btn_restore)

        row1.addWidget(power)
        row1.addWidget(cleanup)
        row1.addWidget(safety)
        root.addLayout(row1)

        # ROW 2 ----------------------------------
        row2 = QHBoxLayout()
        row2.setSpacing(12)

        # MEMORY LEAK
        leak = Card("Memory-Leak Protector")
        lv = leak.body()
        self.btn_ml_start = QPushButton("Start (Fortnite, 1024 MB)")
        self.btn_ml_stop = QPushButton("Stop")
        lv.addWidget(self.btn_ml_start)
        lv.addWidget(self.btn_ml_stop)

        # NETWORK
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

        # STARTUP
        startup = Card("Startup Optimizer")
        sv2 = startup.body()
        self.btn_list_startup = QPushButton("List Startup Entries")
        sv2.addWidget(self.btn_list_startup)

        row2.addWidget(leak)
        row2.addWidget(net)
        row2.addWidget(startup)
        root.addLayout(row2)

        # STORAGE ANALYZER ------------------------
        storage = Card("Storage Analyzer")
        st = storage.body()

        self.btn_analyze_drive = QPushButton("Analyze Disk Usage")
        self.btn_top25 = QPushButton("Analyze Largest 25 Files")
        self.btn_top_dirs = QPushButton("Analyze Largest Directories")
        self.btn_clear_cache = QPushButton("Clear Browser + Store Cache")

        st.addWidget(self.btn_analyze_drive)
        st.addWidget(self.btn_top25)
        st.addWidget(self.btn_top_dirs)
        st.addWidget(self.btn_clear_cache)

        root.addWidget(storage)

        # PROFILE MANAGER -------------------------
        prof = Card("Profile Manager")
        pf = prof.body()

        self.btn_prof_game = QPushButton("Apply Gaming Profile")
        self.btn_prof_prod = QPushButton("Apply Productivity Profile")
        self.btn_prof_stream = QPushButton("Apply Streaming Profile")
        self.btn_prof_save = QPushButton("Save Current As Profile…")
        self.btn_prof_load = QPushButton("Load Custom Profile…")

        for w in (
            self.btn_prof_game,
            self.btn_prof_prod,
            self.btn_prof_stream,
            self.btn_prof_save,
            self.btn_prof_load,
        ):
            w.setMinimumHeight(34)
            pf.addWidget(w)

        root.addWidget(prof)

        # ADVANCED TOOLS --------------------------
        repair_card = Card("System RepairOps")
        rv = repair_card.body()

        self.btn_repair_wu = QPushButton("Repair Windows Update")
        self.btn_reset_net = QPushButton("Reset Network Stack")
        self.btn_dism_sfc = QPushButton("Run DISM + SFC Repair")
        self.btn_reset_store = QPushButton("Reset Microsoft Store Cache")

        for b in (
            self.btn_repair_wu,
            self.btn_reset_net,
            self.btn_dism_sfc,
            self.btn_reset_store,
        ):
            b.setMinimumHeight(34)
            rv.addWidget(b)

        root.addWidget(repair_card)

        # DEBLOAT
        debloat_card = Card("Safe Debloat")
        dv = debloat_card.body()

        self.btn_debloat_xbox = QPushButton("Disable Xbox Game Bar / DVR")
        self.btn_debloat_bg = QPushButton("Disable Background Apps")
        self.btn_debloat_telemetry = QPushButton("Disable Telemetry Tasks (safe)")
        self.btn_debloat_cortana = QPushButton("Limit Cortana / Search Indexing")
        self.btn_debloat_revert = QPushButton("Revert Safe Debloat Profile")

        for b in (
            self.btn_debloat_xbox,
            self.btn_debloat_bg,
            self.btn_debloat_telemetry,
            self.btn_debloat_cortana,
            self.btn_debloat_revert,
        ):
            b.setMinimumHeight(34)
            dv.addWidget(b)

        root.addWidget(debloat_card)

        # UI TWEAKS
        ui_card = Card("Taskbar & Explorer Tweaks")
        uv = ui_card.body()

        self.btn_ui_disable_bing = QPushButton("Disable Bing / Web in Start Search")
        self.btn_ui_disable_widgets = QPushButton("Hide Widgets")
        self.btn_ui_disable_chat = QPushButton("Hide Chat Icon")
        self.btn_ui_explorer_thispc = QPushButton("Open Explorer in 'This PC'")
        self.btn_ui_show_ext = QPushButton("Show File Extensions")
        self.btn_ui_restore_ui = QPushButton("Restore UI Defaults")

        for b in (
            self.btn_ui_disable_bing,
            self.btn_ui_disable_widgets,
            self.btn_ui_disable_chat,
            self.btn_ui_explorer_thispc,
            self.btn_ui_show_ext,
            self.btn_ui_restore_ui,
        ):
            b.setMinimumHeight(34)
            uv.addWidget(b)

        root.addWidget(ui_card)

        # BACKUP
        backup_card = Card("Backup & Restore")
        bv = backup_card.body()

        self.btn_backup_create = QPushButton("Create Backup Snapshot")
        self.btn_backup_restore = QPushButton("Restore Latest Backup")
        self.btn_backup_open = QPushButton("Open Backup Folder")

        for b in (
            self.btn_backup_create,
            self.btn_backup_restore,
            self.btn_backup_open,
        ):
            b.setMinimumHeight(34)
            bv.addWidget(b)

        root.addWidget(backup_card)

        root.addStretch()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(scroll)

        self._connect()

    # SIGNALS ------------------------------------
    def _connect(self):
        # scan
        self.btn_scan.clicked.connect(self._scan)

        # cleanup
        self.btn_clean.clicked.connect(self._clean)
        self.btn_deep_clean.clicked.connect(self._deep_clean)

        # safety
        self.btn_restore.clicked.connect(self._restore)

        # power
        self.btn_plan.clicked.connect(self._plan)

        # mem leak
        self.btn_ml_start.clicked.connect(self._ml_start)
        self.btn_ml_stop.clicked.connect(self._ml_stop)

        # network
        self.btn_dns_cf.clicked.connect(lambda: self._dns("1.1.1.1", "1.0.0.1"))
        self.btn_dns_gg.clicked.connect(lambda: self._dns("8.8.8.8", "8.8.4.4"))
        self.btn_ctcp_on.clicked.connect(lambda: self._ctcp(True))
        self.btn_ctcp_off.clicked.connect(lambda: self._ctcp(False))
        self.btn_auto_norm.clicked.connect(lambda: self._autotune("normal"))
        self.btn_auto_restr.clicked.connect(lambda: self._autotune("restricted"))
        self.btn_nagle_off.clicked.connect(self._nagle_off)
        self.btn_ping.clicked.connect(self._ping)

        # startup
        self.btn_list_startup.clicked.connect(self._startup_list)

        # storage
        self.btn_analyze_drive.clicked.connect(self._analyze_drive)
        self.btn_top25.clicked.connect(self._top25)
        self.btn_top_dirs.clicked.connect(self._top_dirs)
        self.btn_clear_cache.clicked.connect(self._clear_cache)

        # profiles
        self.btn_prof_game.clicked.connect(lambda: self._apply_profile("gaming"))
        self.btn_prof_prod.clicked.connect(lambda: self._apply_profile("productivity"))
        self.btn_prof_stream.clicked.connect(lambda: self._apply_profile("streaming"))
        self.btn_prof_save.clicked.connect(self._save_profile)
        self.btn_prof_load.clicked.connect(self._load_profile)

        # repairops
        self.btn_repair_wu.clicked.connect(self._repair_wu)
        self.btn_reset_net.clicked.connect(self._reset_net)
        self.btn_dism_sfc.clicked.connect(self._run_dism_sfc)
        self.btn_reset_store.clicked.connect(self._reset_store_cache)

        # debloat
        self.btn_debloat_xbox.clicked.connect(self._debloat_xbox)
        self.btn_debloat_bg.clicked.connect(self._debloat_bg_apps)
        self.btn_debloat_telemetry.clicked.connect(self._debloat_telemetry)
        self.btn_debloat_cortana.clicked.connect(self._debloat_cortana)
        self.btn_debloat_revert.clicked.connect(self._debloat_revert)

        # ui tweaks
        self.btn_ui_disable_bing.clicked.connect(self._ui_disable_bing)
        self.btn_ui_disable_widgets.clicked.connect(self._ui_disable_widgets)
        self.btn_ui_disable_chat.clicked.connect(self._ui_disable_chat)
        self.btn_ui_explorer_thispc.clicked.connect(self._ui_explorer_thispc)
        self.btn_ui_show_ext.clicked.connect(self._ui_show_ext)
        self.btn_ui_restore_ui.clicked.connect(self._ui_restore_ui)

        # backup
        self.btn_backup_create.clicked.connect(self._backup_create)
        self.btn_backup_restore.clicked.connect(self._backup_restore)
        self.btn_backup_open.clicked.connect(self._backup_open)

    # LOGIC --------------------------------------

    def _scan(self):
        self.spinner.show()
        self.log.clear()
        self.log.append(self.opt.quick_scan())
        self.spinner.hide()

    def _clean(self):
        n = self.opt.cleanup_temp_files()
        self.log.append(f"[Cleanup] Removed ~{n} files.")

    def _deep_clean(self):
        n = self.opt.deep_cleanup()
        self.log.append(f"[Deep Cleanup] Removed {n} items.")

    def _restore(self):
        ok, msg = self.opt.create_restore_point("QrsTweaks Restore")
        self.log.append(f"[Restore] {msg}")

    def _plan(self):
        ok, msg = self.opt.create_high_perf_powerplan()
        self.log.append(f"[Power] {msg}")

    def _ml_start(self):
        ok, msg = self.opt.start_memleak_protector(
            process_names=["FortniteClient-Win64-Shipping.exe"], mb_threshold=1024
        )
        self.log.append(f"[MemLeak] {msg}")

    def _ml_stop(self):
        ok, msg = self.opt.stop_memleak_protector()
        self.log.append(f"[MemLeak] {msg}")

    def _dns(self, p, s):
        ok, msg = self.opt.set_dns(p, s)
        self.log.append(f"[DNS] {msg}")

    def _ctcp(self, enable):
        ok, msg = self.opt.enable_ctcp(enable)
        self.log.append(f"[CTCP] {msg}")

    def _autotune(self, level):
        ok, msg = self.opt.autotuning(level)
        self.log.append(f"[TCP] {msg}")

    def _nagle_off(self):
        ok, msg = self.opt.toggle_nagle(False)
        self.log.append(f"[Nagle] {msg}")

    def _ping(self):
        ok, out = self.opt.latency_ping("1.1.1.1", 5)
        self.log.append(out)

    def _startup_list(self):
        items = self.opt.list_startup_entries()
        if not items:
            self.log.append("No startup entries found.")
            return
        self.log.append("Startup Entries:")
        for loc, name, val in items:
            self.log.append(f"- {name} → {val}")

    # STORAGE
    def _analyze_drive(self):
        result = self.opt.analyze_drive()
        self.log.append(result)

    def _top25(self):
        result = self.opt.analyze_top25()
        self.log.append(result)

    def _top_dirs(self):
        result = self.opt.analyze_top_dirs()
        self.log.append(result)

    def _clear_cache(self):
        result = self.opt.clear_cache()
        self.log.append(result)

    # PROFILES
    def _apply_profile(self, name: str):
        msgs = []

        if name == "gaming":
            ok, m = self.opt.create_high_perf_powerplan()
            msgs.append(f"[Power] {m}")

            ok, m = self.opt.set_dns("1.1.1.1", "1.0.0.1")
            msgs.append(f"[DNS] {m}")

            ok, m = self.opt.enable_ctcp(True)
            msgs.append(f"[CTCP] {m}")

            ok, m = self.opt.autotuning("restricted")
            msgs.append(f"[TCP] {m}")

            ok, m = self.opt.toggle_nagle(False)
            msgs.append(f"[Nagle] {m}")

            header = "[Profile] Applied Gaming preset"

        elif name == "productivity":
            ok, m = self.opt.autotuning("normal")
            msgs.append(f"[TCP] {m}")

            ok, m = self.opt.enable_ctcp(False)
            msgs.append(f"[CTCP] {m}")

            try:
                ok, m = self.opt.toggle_nagle(True)
                msgs.append(f"[Nagle] {m}")
            except TypeError:
                msgs.append("[Nagle] Left at current setting")

            header = "[Profile] Applied Productivity preset"

        elif name == "streaming":
            ok, m = self.opt.create_high_perf_powerplan()
            msgs.append(f"[Power] {m}")

            ok, m = self.opt.autotuning("normal")
            msgs.append(f"[TCP] {m}")

            ok, m = self.opt.enable_ctcp(True)
            msgs.append(f"[CTCP] {m}")

            header = "[Profile] Applied Streaming preset"

        else:
            self.log.append(f"[Profile] Unknown profile '{name}'")
            return

        self.log.append(header)
        for line in msgs:
            self.log.append("  " + line)

    def _save_profile(self):
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save QrsTweaks Profile",
            "profile.qrsp",
            "QrsTweaks Profile (*.qrsp);;JSON Files (*.json);;All Files (*.*)",
        )
        if not path:
            self.log.append("[Profile] Save cancelled.")
            return

        ok, msg = self.opt.export_profile(path)
        if ok:
            self.log.append(f"[Profile] Saved to {path}")
        else:
            self.log.append(f"[Profile] Save failed: {msg}")

    def _load_profile(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Load QrsTweaks Profile",
            "",
            "QrsTweaks Profile (*.qrsp);;JSON Files (*.json);;All Files (*.*)",
        )
        if not path:
            self.log.append("[Profile] Load cancelled.")
            return

        ok, msg = self.opt.import_profile(path)
        self.log.append(msg)

    # REPAIR OPS
    def _repair_wu(self):
        ok, msg = self.opt.repair_windows_update()
        self.log.append(msg)

    def _reset_net(self):
        ok, msg = self.opt.reset_network_stack()
        self.log.append(msg)

    def _run_dism_sfc(self):
        ok, msg = self.opt.run_dism_sfc()
        self.log.append(msg)

    def _reset_store_cache(self):
        ok, msg = self.opt.reset_store_cache()
        self.log.append(msg)

    # DEBLOAT
    def _debloat_xbox(self):
        ok, msg = self.opt.debloat_xbox_gamebar()
        self.log.append(msg)

    def _debloat_bg_apps(self):
        ok, msg = self.opt.debloat_background_apps()
        self.log.append(msg)

    def _debloat_telemetry(self):
        ok, msg = self.opt.debloat_telemetry_safe()
        self.log.append(msg)

    def _debloat_cortana(self):
        ok, msg = self.opt.debloat_cortana_search()
        self.log.append(msg)

    def _debloat_revert(self):
        ok, msg = self.opt.debloat_revert_safe()
        self.log.append(msg)

    # UI TWEAKS
    def _ui_disable_bing(self):
        ok, msg = self.opt.ui_disable_bing_search()
        self.log.append(msg)

    def _ui_disable_widgets(self):
        ok, msg = self.opt.ui_hide_widgets()
        self.log.append(msg)

    def _ui_disable_chat(self):
        ok, msg = self.opt.ui_hide_chat_icon()
        self.log.append(msg)

    def _ui_explorer_thispc(self):
        ok, msg = self.opt.ui_explorer_this_pc()
        self.log.append(msg)

    def _ui_show_ext(self):
        ok, msg = self.opt.ui_show_file_extensions()
        self.log.append(msg)

    def _ui_restore_ui(self):
        ok, msg = self.opt.ui_restore_defaults()
        self.log.append(msg)

    # BACKUP
    def _backup_create(self):
        ok, msg = self.opt.create_backup_snapshot()
        self.log.append(msg)

    def _backup_restore(self):
        ok, msg = self.opt.restore_latest_backup()
        self.log.append(msg)

    def _backup_open(self):
        ok, msg = self.opt.open_backup_folder()
        self.log.append(msg)
