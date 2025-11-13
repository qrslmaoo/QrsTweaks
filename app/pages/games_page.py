# app/pages/games_page.py

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTextEdit, QComboBox, QScrollArea
)
from PySide6.QtCore import Qt

from app.ui.widgets.card import Card
from src.qrs.modules.game_optim import GameOptimizer


class GamesPage(QWidget):
    """
    Game Optimizer page

    Layout is intentionally made to mirror WindowsPage:
      - One big title
      - Everything else inside Card widgets
      - Single scroll area with 10px margins and 16px spacing
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background: transparent;")

        self.opt = GameOptimizer()

        # -------------------------------------------------
        # SCROLL WRAPPER (same pattern as WindowsPage)
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

        for b in (self.btn_cpu_high, self.btn_cpu_above, self.btn_toggle_nagle):
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
            "Profiles store per-game optimization choices such as CPU priority, "
            "network settings, shader cache behavior, and storage cleanup rules."
        )
        desc.setWordWrap(True)
        desc.setStyleSheet("color:#AAB0BC; font-size:10pt;")
        prof_body.addWidget(desc)

        self.btn_profile_apply = QPushButton("Apply Current Game Profile")
        self.btn_profile_export = QPushButton("Export Profile to .qrsgame")
        self.btn_profile_import = QPushButton("Import Profile from .qrsgame")

        for b in (
            self.btn_profile_apply,
            self.btn_profile_export,
            self.btn_profile_import,
        ):
            prof_body.addWidget(b)

        root.addWidget(card_prof)

        # Stretch so content hugs the top when short
        root.addStretch()

        # Attach scroll to this widget (same as WindowsPage)
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
        # Game selector profile buttons (UI stubs for now)
        self.btn_load_profile.clicked.connect(
            lambda: self._log("[Game] Load Game Profile… (coming soon)")
        )
        self.btn_save_profile.clicked.connect(
            lambda: self._log("[Game] Save Game Profile… (coming soon)")
        )

        # Fortnite tweaks (real backend logic)
        self.btn_fn_disable_record.clicked.connect(self._fn_disable_record)
        self.btn_fn_clean_logs.clicked.connect(self._fn_clean_logs)
        self.btn_fn_clean_shader.clicked.connect(self._fn_clean_shader)
        self.btn_fn_clean_dx.clicked.connect(self._clean_dx)

        # System tuning – currently stubs
        self.btn_cpu_high.clicked.connect(
            lambda: self._log("[CPU] Set game process priority: HIGH (not implemented yet)")
        )
        self.btn_cpu_above.clicked.connect(
            lambda: self._log("[CPU] Set game process priority: ABOVE NORMAL (not implemented yet)")
        )
        self.btn_toggle_nagle.clicked.connect(
            lambda: self._log("[Network] Disable Nagle per-game (not implemented yet)")
        )

        # Storage tweaks
        self.btn_storage_clean_temp.clicked.connect(self._clean_temp)
        self.btn_storage_clean_crash.clicked.connect(self._clean_crash)
        self.btn_storage_clean_shader.clicked.connect(self._clean_shader)
        self.btn_storage_clean_dx2.clicked.connect(self._clean_dx)
        self.btn_storage_reset_cfg.clicked.connect(self._reset_cfg)

        # Profiles (stubs for now)
        self.btn_profile_apply.clicked.connect(
            lambda: self._log("[Profile] Apply current game profile (coming soon)")
        )
        self.btn_profile_export.clicked.connect(
            lambda: self._log("[Profile] Export profile to .qrsgame (coming soon)")
        )
        self.btn_profile_import.clicked.connect(
            lambda: self._log("[Profile] Import profile from .qrsgame (coming soon)")
        )

    # -------------------------------------------------
    # BACKEND LOGIC HOOKS
    # -------------------------------------------------
    def _fn_disable_record(self):
        ok1, msg1 = self.opt.disable_xbox_game_bar()
        ok2, msg2 = self.opt.disable_game_dvr()
        self._log_result(
            "[Fortnite] Disable Game Bar / DVR",
            ok1 and ok2,
            msg1 + "\n" + msg2,
        )

    def _fn_clean_logs(self):
        ok, msg = self.opt.clean_fortnite_logs_and_crashes()
        self._log_result("[Fortnite] Clean logs & crash dumps", ok, msg)

    def _fn_clean_shader(self):
        ok, msg = self.opt.clean_fortnite_shader_cache()
        self._log_result("[Fortnite] Clean shader / pipeline cache", ok, msg)

    def _clean_dx(self):
        ok, msg = self.opt.clean_directx_cache()
        self._log_result("[DirectX] Cache cleanup", ok, msg)

    # ---- Storage helpers ----
    def _clean_temp(self):
        game = self.combo_game.currentText()
        self._log(f"[Storage] Clean temp files for {game} (not implemented yet)")

    def _clean_crash(self):
        game = self.combo_game.currentText()
        if game == "Fortnite":
            self._fn_clean_logs()
        else:
            self._log(f"[Storage] Crash cleanup not implemented for {game}")

    def _clean_shader(self):
        game = self.combo_game.currentText()
        if game == "Fortnite":
            self._fn_clean_shader()
        else:
            self._log(f"[Storage] Shader cleanup not implemented for {game}")

    def _reset_cfg(self):
        game = self.combo_game.currentText()
        self._log(f"[Storage] Reset config for {game} (coming soon, with backup)")

    # -------------------------------------------------
    # LOGGING HELPERS
    # -------------------------------------------------
    def _log(self, text: str):
        self.log.append(f"<span style='color:#DDE1EA'>{text}</span>")

    def _log_result(self, label: str, ok: bool, msg: str):
        color = "#44dd44" if ok else "#ff4444"
        safe = (
            msg.replace("&", "&amp;")
               .replace("<", "&lt;")
               .replace(">", "&gt;")
        )
        self.log.append(
            f"<span style='color:{color}'>{label}: {safe}</span>"
        )
