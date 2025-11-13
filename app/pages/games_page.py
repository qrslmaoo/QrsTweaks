# app/pages/games_page.py

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTextEdit, QComboBox, QScrollArea
)
from PySide6.QtCore import Qt

from app.ui.widgets.card import Card
from src.qrs.modules.game_optim import GameOptimizer


class GamesPage(QWidget):
    """
    Game Optimizer page.

    Layout is intentionally mirrored to WindowsPage:
      - Top title
      - Scroll area hosting a container widget
      - Cards organized in horizontal rows where appropriate
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background: transparent;")

        self.opt = GameOptimizer()

        # -----------------------------------------------------
        # SCROLL WRAPPER (same pattern as WindowsPage)
        # -----------------------------------------------------
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

        # -----------------------------------------------------
        # PAGE TITLE
        # -----------------------------------------------------
        title = QLabel("Game Optimizer")
        title.setStyleSheet("font-size: 22pt; color: #DDE1EA; font-weight:700;")
        root.addWidget(title)

        # -----------------------------------------------------
        # TARGET GAME (full-width card)
        # -----------------------------------------------------
        sel_card = Card("Target Game")
        sel_body = sel_card.body()

        sel_row = QHBoxLayout()
        sel_row.setSpacing(12)

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

        sel_row.addWidget(self.combo_game)
        sel_row.addStretch()
        sel_row.addWidget(self.btn_load_profile)
        sel_row.addWidget(self.btn_save_profile)

        sel_body.addLayout(sel_row)
        root.addWidget(sel_card)

        # -----------------------------------------------------
        # GAME OPTIMIZATION LOG (full-width card)
        # -----------------------------------------------------
        log_card = Card("Game Optimization Log")
        log_body = log_card.body()

        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setMinimumHeight(200)
        log_body.addWidget(self.log)

        root.addWidget(log_card)

        # -----------------------------------------------------
        # ROW 1: Fortnite Tweaks  |  System Tuning (Per Game)
        # -----------------------------------------------------
        row1 = QHBoxLayout()
        row1.setSpacing(12)

        # Fortnite Tweaks
        fn_card = Card("Fortnite Tweaks")
        fn_body = fn_card.body()

        self.btn_fn_disable_record = QPushButton("Disable Background Recording (Game Bar / DVR)")
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
        tuning_card = Card("System Tuning (Per Game)")
        tune_body = tuning_card.body()

        self.btn_cpu_high = QPushButton("Set Game Process to HIGH Priority")
        self.btn_cpu_above = QPushButton("Set Game Process to ABOVE NORMAL")
        self.btn_toggle_nagle = QPushButton("Disable Nagle (Low-Latency)")

        for b in (
            self.btn_cpu_high,
            self.btn_cpu_above,
            self.btn_toggle_nagle,
        ):
            tune_body.addWidget(b)

        row1.addWidget(fn_card)
        row1.addWidget(tuning_card)
        root.addLayout(row1)

        # -----------------------------------------------------
        # ROW 2: Game Storage Tweaks  |  Game Profiles
        # -----------------------------------------------------
        row2 = QHBoxLayout()
        row2.setSpacing(12)

        # Game Storage Tweaks
        storage_card = Card("Game Storage Tweaks")
        st_body = storage_card.body()

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

        # Game Profiles
        profiles_card = Card("Game Profiles")
        prof_body = profiles_card.body()

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

        prof_body.addWidget(self.btn_profile_apply)
        prof_body.addWidget(self.btn_profile_export)
        prof_body.addWidget(self.btn_profile_import)

        row2.addWidget(storage_card)
        row2.addWidget(profiles_card)
        root.addLayout(row2)

        # Stretch at bottom
        root.addStretch()

        # Attach scroll to this widget
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(scroll)

        # -----------------------------------------------------
        # SIGNAL CONNECTIONS
        # -----------------------------------------------------

        # Target game profile load/save – stubs for now
        self.btn_load_profile.clicked.connect(
            lambda: self._log("[Game] Load Game Profile… (coming soon)")
        )
        self.btn_save_profile.clicked.connect(
            lambda: self._log("[Game] Save Game Profile… (coming soon)")
        )

        # Fortnite / global tweaks (real logic)
        self.btn_fn_disable_record.clicked.connect(self._fn_disable_record)
        self.btn_fn_clean_logs.clicked.connect(self._fn_clean_logs)
        self.btn_fn_clean_shader.clicked.connect(self._fn_clean_shader)
        self.btn_fn_clean_dx.clicked.connect(self._clean_dx)

        # Storage logic (partially implemented)
        self.btn_storage_clean_crash.clicked.connect(self._clean_crash)
        self.btn_storage_clean_shader.clicked.connect(self._clean_shader)
        self.btn_storage_clean_dx2.clicked.connect(self._clean_dx)

        # Stubs for not-yet-implemented actions
        self.btn_cpu_high.clicked.connect(
            lambda: self._log("[CPU] Set game process priority: HIGH (TODO)")
        )
        self.btn_cpu_above.clicked.connect(
            lambda: self._log("[CPU] Set game process priority: ABOVE NORMAL (TODO)")
        )
        self.btn_toggle_nagle.clicked.connect(
            lambda: self._log("[Network] Disable Nagle per-game (TODO)")
        )

        self.btn_storage_clean_temp.clicked.connect(
            lambda: self._log("[Storage] Clean game temp files (TODO)")
        )
        self.btn_storage_reset_cfg.clicked.connect(
            lambda: self._log("[Storage] Reset game config with backup (TODO)")
        )

        self.btn_profile_apply.clicked.connect(
            lambda: self._log("[Profile] Apply current game profile (TODO)")
        )
        self.btn_profile_export.clicked.connect(
            lambda: self._log("[Profile] Export profile to .qrsgame (TODO)")
        )
        self.btn_profile_import.clicked.connect(
            lambda: self._log("[Profile] Import profile from .qrsgame (TODO)")
        )

    # ---------------------------------------------------------
    # BACKEND HOOKS (use src.qrs.modules.game_optim.GameOptimizer)
    # ---------------------------------------------------------

    def _fn_disable_record(self):
        ok1, msg1 = self.opt.disable_xbox_game_bar()
        ok2, msg2 = self.opt.disable_game_dvr()
        self._log_result(
            "[Fortnite] Disable Recording",
            ok1 and ok2,
            msg1 + "\n" + msg2,
        )

    def _fn_clean_logs(self):
        ok, msg = self.opt.clean_fortnite_logs_and_crashes()
        self._log_result("[Fortnite] Clean Logs/Crashes", ok, msg)

    def _fn_clean_shader(self):
        ok, msg = self.opt.clean_fortnite_shader_cache()
        self._log_result("[Fortnite] Clean Shader Cache", ok, msg)

    def _clean_dx(self):
        ok, msg = self.opt.clean_directx_cache()
        self._log_result("[DirectX] Cache Cleanup", ok, msg)

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

    # ---------------------------------------------------------
    # LOGGING HELPERS
    # ---------------------------------------------------------

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
            f"<span style='color:{color}'>{label}:<br>{safe}</span>"
        )
