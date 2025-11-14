# app/pages/games_page.py

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTextEdit, QComboBox, QScrollArea
)
from PySide6.QtCore import Qt, QTimer

from app.ui.widgets.card import Card
from src.qrs.modules.game_optim import GameOptimizer
from src.qrs.core.log_manager import log_mgr


class GamesPage(QWidget):
    """
    Game Optimizer page

    Layout mirrors WindowsPage:
      - One big title
      - Everything else inside Card widgets
      - Single scroll area with 10px margins and 16px spacing

    Phase 6+ additions:
      - Smart Game Mode (auto-apply tweaks when game starts)
      - Real CPU priority / affinity wiring
      - Fortnite preset integration
      - Global logging via LogManager
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background: transparent;")

        self.opt = GameOptimizer()

        # Smart Game Mode state
        self.auto_enabled = False
        self.auto_timer = QTimer(self)
        self.auto_timer.setInterval(3000)  # check every 3s
        self.auto_timer.timeout.connect(self._auto_tick)
        self._auto_last_pid = None

        # -------------------------------------------------
        # SCROLL WRAPPER
        # -------------------------------------------------
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setFrameShape(QScrollArea.NoFrame)
        scroll.setStyleSheet("background: transparent;")

        container = QWidget()
        scroll.setWidget(container)

        root = QVBoxLayout(container)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(16)

        # -------------------------------------------------
        # PAGE TITLE
        # -------------------------------------------------
        title = QLabel("Game Optimizer")
        title.setStyleSheet("font-size: 22pt; color: #DDE1EA; font-weight: 700;")
        root.addWidget(title)

        # -------------------------------------------------
        # TARGET GAME (Card)
        # -------------------------------------------------
        card_select = Card("Target Game")
        sel_body = card_select.body()

        row_sel = QHBoxLayout()
        row_sel.setSpacing(12)

        self.combo_game = QComboBox()
        self.combo_game.addItems([
            "Fortnite",
            "Minecraft",
            "Valorant",
            "Call of Duty",
            "Custom Game…",
        ])
        self.combo_game.setFixedWidth(220)

        self.btn_load_profile = QPushButton("Load Game Profile…")
        self.btn_save_profile = QPushButton("Save Game Profile…")

        row_sel.addWidget(self.combo_game)
        row_sel.addStretch()
        row_sel.addWidget(self.btn_load_profile)
        row_sel.addWidget(self.btn_save_profile)

        sel_body.addLayout(row_sel)
        root.addWidget(card_select)

        # -------------------------------------------------
        # GAME OPTIMIZATION LOG (Card)
        # -------------------------------------------------
        card_log = Card("Game Optimization Log")
        log_body = card_log.body()

        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setMinimumHeight(180)
        log_body.addWidget(self.log)

        root.addWidget(card_log)

        # -------------------------------------------------
        # SMART GAME MODE (auto-apply on game start)
        # -------------------------------------------------
        card_auto = Card("Smart Game Mode")
        auto_body = card_auto.body()

        self.btn_auto = QPushButton("Smart Game Mode: OFF")
        self.lbl_auto = QLabel(
            "When enabled, QrsTweaks will watch for the selected game to start.\n"
            "- Fortnite → applies Fortnite Gaming Preset automatically.\n"
            "- Other games → HIGH process priority + recommended cores."
        )
        self.lbl_auto.setWordWrap(True)
        self.lbl_auto.setStyleSheet("color:#AAB0BC; font-size:10pt;")

        auto_body.addWidget(self.btn_auto)
        auto_body.addWidget(self.lbl_auto)

        root.addWidget(card_auto)

        # -------------------------------------------------
        # FORTNITE TWEAKS + SYSTEM TUNING (ROW OF CARDS)
        # -------------------------------------------------
        row_ft = QHBoxLayout()
        row_ft.setSpacing(12)

        # Fortnite Tweaks
        card_fn = Card("Fortnite Tweaks")
        fn_body = card_fn.body()

        self.btn_fn_disable_record = QPushButton(
            "Disable Background Recording (Game Bar / DVR)"
        )
        self.btn_fn_clean_logs = QPushButton("Clean Fortnite Logs & Crash Dumps")
        self.btn_fn_clean_shader = QPushButton("Clean Shader / Pipeline Caches")
        self.btn_fn_clean_dx = QPushButton("Clean DirectX Cache (Game Scope)")

        for b in (
            self.btn_fn_disable_record,
            self.btn_fn_clean_logs,
            self.btn_fn_clean_shader,
            self.btn_fn_clean_dx,
        ):
            fn_body.addWidget(b)

        # System Tuning (Per Game)
        card_tuning = Card("System Tuning (Per Game)")
        tune_body = card_tuning.body()

        self.btn_cpu_high = QPushButton("Set Game Process to HIGH Priority")
        self.btn_cpu_above = QPushButton("Set Game Process to ABOVE NORMAL")
        self.btn_toggle_nagle = QPushButton("Disable Nagle (Low-Latency)")
        self.btn_affinity_recommended = QPushButton("Bind Game to Recommended Cores")
        self.btn_affinity_all = QPushButton("Bind Game to All Cores")

        for b in (
            self.btn_cpu_high,
            self.btn_cpu_above,
            self.btn_toggle_nagle,
            self.btn_affinity_recommended,
            self.btn_affinity_all,
        ):
            tune_body.addWidget(b)

        row_ft.addWidget(card_fn)
        row_ft.addWidget(card_tuning)
        root.addLayout(row_ft)

        # -------------------------------------------------
        # GAME STORAGE TWEAKS (Card)
        # -------------------------------------------------
        card_store = Card("Game Storage Tweaks")
        st_body = card_store.body()

        self.btn_storage_clean_temp = QPushButton("Clean Game Temp Files")
        self.btn_storage_clean_crash = QPushButton("Clean Game Crash Dumps")
        self.btn_storage_clean_shader = QPushButton("Clean Shader / Pipeline Caches")
        self.btn_storage_clean_dx2 = QPushButton("Clean DirectX Cache (Global)")
        self.btn_storage_reset_cfg = QPushButton("Reset Game Config (Backup First)")

        for b in (
            self.btn_storage_clean_temp,
            self.btn_storage_clean_crash,
            self.btn_storage_clean_shader,
            self.btn_storage_clean_dx2,
            self.btn_storage_reset_cfg,
        ):
            st_body.addWidget(b)

        root.addWidget(card_store)

        # -------------------------------------------------
        # GAME PROFILES (Card)
        # -------------------------------------------------
        card_prof = Card("Game Profiles")
        prof_body = card_prof.body()

        desc = QLabel(
            "Profiles will store per-game optimization choices such as CPU priority, "
            "network settings, shader cache behavior, and storage cleanup rules.\n"
            "Basic Fortnite preset is available now; full export/import is coming later."
        )
        desc.setWordWrap(True)
        desc.setStyleSheet("color:#AAB0BC; font-size:10pt;")
        prof_body.addWidget(desc)

        self.btn_profile_apply = QPushButton("Apply Current Game Profile")
        self.btn_profile_export = QPushButton("Export Profile to .qrsgame (coming soon)")
        self.btn_profile_import = QPushButton("Import Profile from .qrsgame (coming soon)")

        for b in (
            self.btn_profile_apply,
            self.btn_profile_export,
            self.btn_profile_import,
        ):
            prof_body.addWidget(b)

        root.addWidget(card_prof)

        root.addStretch()

        # Attach scroll to this widget
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        main_layout.addWidget(scroll)

        # Wire signals
        self._connect()

    # -------------------------------------------------
    # SIGNAL CONNECTIONS
    # -------------------------------------------------
    def _connect(self):
        # Game selector profile buttons (still basic for now)
        self.btn_load_profile.clicked.connect(
            lambda: self._log("[Game] Load Game Profile… (not implemented yet)")
        )
        self.btn_save_profile.clicked.connect(
            lambda: self._log("[Game] Save Game Profile… (not implemented yet)")
        )

        # Smart Game Mode
        self.btn_auto.clicked.connect(self._toggle_auto)

        # Fortnite tweaks
        self.btn_fn_disable_record.clicked.connect(self._fn_disable_record)
        self.btn_fn_clean_logs.clicked.connect(self._fn_clean_logs)
        self.btn_fn_clean_shader.clicked.connect(self._fn_clean_shader)
        self.btn_fn_clean_dx.clicked.connect(self._clean_dx)

        # System tuning
        self.btn_cpu_high.clicked.connect(self._cpu_high)
        self.btn_cpu_above.clicked.connect(self._cpu_above)
        self.btn_toggle_nagle.clicked.connect(self._nagle_stub)
        self.btn_affinity_recommended.clicked.connect(self._affinity_recommended)
        self.btn_affinity_all.clicked.connect(self._affinity_all)

        # Storage tweaks
        self.btn_storage_clean_temp.clicked.connect(self._clean_temp)
        self.btn_storage_clean_crash.clicked.connect(self._clean_crash)
        self.btn_storage_clean_shader.clicked.connect(self._clean_shader)
        self.btn_storage_clean_dx2.clicked.connect(self._clean_dx)
        self.btn_storage_reset_cfg.clicked.connect(self._reset_cfg)

        # Profiles
        self.btn_profile_apply.clicked.connect(self._apply_current_profile)
        self.btn_profile_export.clicked.connect(
            lambda: self._log("[Profile] Export to .qrsgame not implemented yet.")
        )
        self.btn_profile_import.clicked.connect(
            lambda: self._log("[Profile] Import from .qrsgame not implemented yet.")
        )

    # -------------------------------------------------
    # BACKEND LOGIC HOOKS
    # -------------------------------------------------
    def _fn_disable_record(self):
        ok1, msg1 = self.opt.disable_xbox_game_bar()
        ok2, msg2 = self.opt.disable_game_dvr()
        combined = msg1 + "\n" + msg2
        self._log_result(
            "[Fortnite] Disable Game Bar / DVR",
            ok1 and ok2,
            combined,
        )
        log_mgr.log("Game", "Disabled Xbox Game Bar / Game DVR.", level="ok" if (ok1 and ok2) else "warn")

    def _fn_clean_logs(self):
        ok, msg = self.opt.clean_fortnite_logs_and_crashes()
        self._log_result("[Fortnite] Clean logs & crash dumps", ok, msg)
        log_mgr.log("Game", "Fortnite logs/crashes cleanup run.", level="ok" if ok else "warn")

    def _fn_clean_shader(self):
        ok, msg = self.opt.clean_fortnite_shader_cache()
        self._log_result("[Fortnite] Clean shader / pipeline cache", ok, msg)
        log_mgr.log("Game", "Fortnite shader cache cleanup run.", level="ok" if ok else "warn")

    def _clean_dx(self):
        ok, msg = self.opt.clean_directx_cache()
        self._log_result("[DirectX] Cache cleanup", ok, msg)
        log_mgr.log("Game", "DirectX cache cleanup run.", level="ok" if ok else "warn")

    # ---- System tuning helpers ----
    def _cpu_high(self):
        game = self.combo_game.currentText()
        ok, msg = self.opt.apply_game_priority(game, "HIGH")
        self._log_result(f"[CPU] {game} → HIGH priority", ok, msg)
        log_mgr.log("Game", f"{game}: HIGH priority applied.", level="ok" if ok else "warn", bubble=ok)

    def _cpu_above(self):
        game = self.combo_game.currentText()
        ok, msg = self.opt.apply_game_priority(game, "ABOVE_NORMAL")
        self._log_result(f"[CPU] {game} → ABOVE NORMAL priority", ok, msg)
        log_mgr.log("Game", f"{game}: ABOVE NORMAL priority applied.", level="ok" if ok else "warn")

    def _nagle_stub(self):
        txt = (
            "[Network] Per-game Nagle toggle is not implemented yet.\n"
            "Use Windows Optimizer → Network Optimizer → 'Disable Nagle (gaming)'."
        )
        self._log(txt)
        log_mgr.log("Game", "Per-game Nagle toggle not yet implemented.", level="info")

    def _affinity_recommended(self):
        game = self.combo_game.currentText()
        ok, msg = self.opt.apply_game_affinity_recommended(game)
        self._log_result(f"[CPU] {game} → recommended cores", ok, msg)
        log_mgr.log("Game", f"{game}: recommended core affinity applied.", level="ok" if ok else "warn")

    def _affinity_all(self):
        game = self.combo_game.currentText()
        ok, msg = self.opt.apply_game_affinity_all_cores(game)
        self._log_result(f"[CPU] {game} → all cores", ok, msg)
        log_mgr.log("Game", f"{game}: all-core affinity applied.", level="ok" if ok else "warn")

    # ---- Storage helpers ----
    def _clean_temp(self):
        game = self.combo_game.currentText()
        msg = f"[Storage] Clean temp files for {game} (not implemented yet)"
        self._log(msg)
        log_mgr.log("Game", f"Temp cleanup stub invoked for {game}.", level="info")

    def _clean_crash(self):
        game = self.combo_game.currentText()
        if game == "Fortnite":
            self._fn_clean_logs()
        else:
            msg = f"[Storage] Crash cleanup not implemented for {game}"
            self._log(msg)
            log_mgr.log("Game", msg, level="info")

    def _clean_shader(self):
        game = self.combo_game.currentText()
        if game == "Fortnite":
            self._fn_clean_shader()
        else:
            msg = f"[Storage] Shader cleanup not implemented for {game}"
            self._log(msg)
            log_mgr.log("Game", msg, level="info")

    def _reset_cfg(self):
        game = self.combo_game.currentText()
        msg = f"[Storage] Reset config for {game} (planned with backup soon)"
        self._log(msg)
        log_mgr.log("Game", msg, level="info")

    # ---- Profiles ----
    def _apply_current_profile(self):
        game = self.combo_game.currentText()
        if game == "Fortnite":
            ok, msg = self.opt.apply_fortnite_gaming_preset()
            self._log_result("[Profile] Fortnite Gaming preset", ok, msg)
            log_mgr.log("Game", "Fortnite Gaming preset applied via GamePage.", level="ok" if ok else "warn", bubble=ok)
        else:
            ok1, msg1 = self.opt.apply_game_priority(game, "HIGH")
            ok2, msg2 = self.opt.apply_game_affinity_recommended(game)
            self._log_result(f"[Profile] {game} priority preset", ok1, msg1)
            self._log_result(f"[Profile] {game} core preset", ok2, msg2)
            log_mgr.log("Game", f"{game}: profile applied (HIGH + recommended cores).", level="ok" if (ok1 and ok2) else "warn")

    # -------------------------------------------------
    # SMART GAME MODE (AUTO ENGINE)
    # -------------------------------------------------
    def _toggle_auto(self):
        self.auto_enabled = not self.auto_enabled
        game = self.combo_game.currentText()

        if self.auto_enabled:
            self.auto_timer.start()
            self.btn_auto.setText("Smart Game Mode: ON")
            self._log(
                f"[AutoGame] Smart Game Mode enabled for '{game}'. "
                "QrsTweaks will auto-apply presets when the game starts."
            )
            log_mgr.log("Game", f"Smart Game Mode enabled for {game}.", level="info", bubble=True)
            self._auto_last_pid = None
        else:
            self.auto_timer.stop()
            self.btn_auto.setText("Smart Game Mode: OFF")
            self._log(f"[AutoGame] Smart Game Mode disabled for '{game}'.")
            log_mgr.log("Game", f"Smart Game Mode disabled for {game}.", level="info")
            self._auto_last_pid = None

    def _auto_tick(self):
        if not self.auto_enabled:
            return

        game = self.combo_game.currentText()
        if game == "Custom Game…":
            return

        pid = self.opt.get_game_pid_or_none(game)

        if pid is None:
            if self._auto_last_pid is not None:
                self._log(f"[AutoGame] '{game}' no longer detected.")
                log_mgr.log("Game", f"{game} no longer detected (Smart Mode).", level="info")
                self._auto_last_pid = None
            return

        if self._auto_last_pid != pid:
            self._auto_last_pid = pid
            self._log(f"[AutoGame] Detected '{game}' (PID {pid}). Applying presets…")
            log_mgr.log("Game", f"{game} detected (PID {pid}), applying Smart presets.", level="ok", bubble=True)

            if game.startswith("Fortnite"):
                ok, msg = self.opt.apply_fortnite_gaming_preset()
                self._log_result("[AutoGame] Fortnite Gaming preset", ok, msg)
                log_mgr.log("Game", "Fortnite Gaming preset auto-applied.", level="ok" if ok else "warn")
            else:
                ok1, msg1 = self.opt.apply_game_priority(game, "HIGH")
                ok2, msg2 = self.opt.apply_game_affinity_recommended(game)
                self._log_result(f"[AutoGame] {game} → HIGH priority", ok1, msg1)
                self._log_result(f"[AutoGame] {game} → recommended cores", ok2, msg2)
                log_mgr.log("Game", f"{game}: Smart Mode applied (HIGH + recommended cores).", level="ok" if (ok1 and ok2) else "warn")

    # -------------------------------------------------
    # LOGGING HELPERS
    # -------------------------------------------------
    def _log(self, text: str):
        safe = (
            text.replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
        )
        self.log.append(f"<span style='color:#DDE1EA'>{safe}</span>")

    def _log_result(self, label: str, ok: bool, msg: str):
        color = "#44dd44" if ok else "#ff4444"
        safe = (
            msg.replace("&", "&amp;")
               .replace("<", "&lt;")
               .replace(">", "&gt;")
        )
        safe_label = (
            label.replace("&", "&amp;")
                 .replace("<", "&lt;")
                 .replace(">", "&gt;")
        )
        self.log.append(
            f"<span style='color:{color}'>{safe_label}: {safe}</span>"
        )
