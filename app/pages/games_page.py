# app/pages/games_page.py

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTextEdit, QComboBox, QScrollArea,
    QFileDialog
)
from PySide6.QtCore import Qt

from pathlib import Path

from app.ui.widgets.card import Card
from src.qrs.modules.game_optim import GameOptimizer
from src.qrs.modules.game_profile import (
    GameProfile,
    load_game_profile,
    save_game_profile,
    apply_game_profile,
)


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
        self._current_profile: GameProfile | None = None

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
        # Game selector profile buttons

        # Load from built-in presets folder: profiles/games
        self.btn_load_profile.clicked.connect(self._load_builtin_profile)

        # Save = export current active profile (if any)
        self.btn_save_profile.clicked.connect(self._export_profile_dialog)

        # Fortnite tweaks (real backend logic)
        self.btn_fn_disable_record.clicked.connect(self._fn_disable_record)
        self.btn_fn_clean_logs.clicked.connect(self._fn_clean_logs)
        self.btn_fn_clean_shader.clicked.connect(self._fn_clean_shader)
        self.btn_fn_clean_dx.clicked.connect(self._clean_dx)

        # System tuning – now use GameOptimizer backend
        self.btn_cpu_high.clicked.connect(self._set_high_priority)
        self.btn_cpu_above.clicked.connect(self._set_above_priority)
        self.btn_toggle_nagle.clicked.connect(
            lambda: self._log("[Network] Per-game Nagle toggle not implemented yet (global Nagle is on Windows page).")
        )

        # Storage tweaks
        self.btn_storage_clean_temp.clicked.connect(self._clean_temp)
        self.btn_storage_clean_crash.clicked.connect(self._clean_crash)
        self.btn_storage_clean_shader.clicked.connect(self._clean_shader)
        self.btn_storage_clean_dx2.clicked.connect(self._clean_dx)
        self.btn_storage_reset_cfg.clicked.connect(self._reset_cfg)

        # Profiles
        self.btn_profile_apply.clicked.connect(self._apply_current_profile)
        self.btn_profile_export.clicked.connect(self._export_profile_dialog)
        self.btn_profile_import.clicked.connect(self._import_profile_dialog)

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

    # ---- System tuning helpers ----
    def _current_game_label(self) -> str:
        text = self.combo_game.currentText() or ""
        return text.strip() or "Custom Game…"

    def _set_high_priority(self):
        game = self._current_game_label()
        ok, msg = self.opt.apply_game_priority(game, "HIGH")
        self._log_result(f"[CPU] HIGH priority for {game}", ok, msg)

    def _set_above_priority(self):
        game = self._current_game_label()
        ok, msg = self.opt.apply_game_priority(game, "ABOVE_NORMAL")
        self._log_result(f"[CPU] ABOVE NORMAL priority for {game}", ok, msg)

    # ---- Storage helpers ----
    def _clean_temp(self):
        game = self._current_game_label()
        self._log(f"[Storage] Clean temp files for {game} (not implemented yet)")

    def _clean_crash(self):
        game = self._current_game_label()
        if game.lower().startswith("fortnite"):
            self._fn_clean_logs()
        else:
            self._log(f"[Storage] Crash cleanup not implemented for {game}")

    def _clean_shader(self):
        game = self._current_game_label()
        if game.lower().startswith("fortnite"):
            self._fn_clean_shader()
        else:
            self._log(f"[Storage] Shader cleanup not implemented for {game}")

    def _reset_cfg(self):
        game = self._current_game_label()
        self._log(f"[Storage] Reset config for {game} (coming soon, with backup)")

    # -------------------------------------------------
    # PROFILE HANDLERS
    # -------------------------------------------------
    def _profiles_folder(self) -> Path:
        """
        Default folder for built-in game profiles.
        """
        return Path.cwd() / "profiles" / "games"

    def _load_builtin_profile(self):
        """
        Open a file dialog rooted at profiles/games and load a .qrsgame.
        """
        base = self._profiles_folder()
        start_dir = str(base) if base.exists() else ""

        path, _ = QFileDialog.getOpenFileName(
            self,
            "Load Game Profile",
            start_dir,
            "QrsTweaks Game Profile (*.qrsgame);;JSON Files (*.json);;All Files (*.*)",
        )
        if not path:
            self._log("[Profile] Load cancelled.")
            return

        self._load_profile_from_path(Path(path))

    def _import_profile_dialog(self):
        """
        Import a profile from any location (same loader as above, but no default dir).
        """
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Import Game Profile",
            "",
            "QrsTweaks Game Profile (*.qrsgame);;JSON Files (*.json);;All Files (*.*)",
        )
        if not path:
            self._log("[Profile] Import cancelled.")
            return

        self._load_profile_from_path(Path(path))

    def _load_profile_from_path(self, path: Path):
        ok, msg, profile = load_game_profile(path)
        color = "#44dd44" if ok else "#ffcc44"

        # Log result
        safe_msg = (
            msg.replace("&", "&amp;")
               .replace("<", "&lt;")
               .replace(">", "&gt;")
        )
        self.log.append(
            f"<span style='color:{color}'>{safe_msg}</span>"
        )

        if profile is None:
            return

        self._current_profile = profile

        # Try to align combobox with profile.game_label
        label = (profile.game_label or "").strip()
        if label:
            label_lower = label.lower()
            for i in range(self.combo_game.count()):
                item = self.combo_game.itemText(i) or ""
                if label_lower in item.lower():
                    self.combo_game.setCurrentIndex(i)
                    break

        self._log(f"[Profile] Active profile set to '{profile.name}' ({profile.game_label}).")

    def _apply_current_profile(self):
        """
        Apply the currently loaded profile via GameOptimizer.
        """
        if self._current_profile is None:
            self._log("[Profile] No active game profile. Load or import one first.")
            return

        game = self._current_game_label()
        ok, msg = apply_game_profile(self._current_profile, game, self.opt)
        self._log_result("[Profile] Apply current profile", ok, msg)

    def _export_profile_dialog(self):
        """
        Export the currently active GameProfile to a .qrsgame file.
        """
        if self._current_profile is None:
            self._log("[Profile] No active game profile to export.")
            return

        base_name = f"{self._current_profile.name or 'GameProfile'}.qrsgame"
        folder = self._profiles_folder()
        folder.mkdir(parents=True, exist_ok=True)

        path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Game Profile",
            str(folder / base_name),
            "QrsTweaks Game Profile (*.qrsgame);;JSON Files (*.json);;All Files (*.*)",
        )
        if not path:
            self._log("[Profile] Export cancelled.")
            return

        ok, msg = save_game_profile(path, self._current_profile)
        self._log_result("[Profile] Export", ok, msg)

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
