# app/pages/games_page.py
import json
from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFileDialog, QTextEdit
)
from PySide6.QtCore import Qt
from app.ui.widgets.card import Card
from app.ui.animations import fade_in, slide_in_y
from src.qrs.modules.windows_optim import WindowsOptimizer


class GamesPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background: transparent;")
        self.opt = WindowsOptimizer()
        self.loaded_profile = None
        self.loaded_path = None

        root = QVBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(12)

        # Header
        header = QLabel("Game Optimizer")
        header.setStyleSheet("color:#DDE1EA; font-size:20pt; font-weight:700;")
        root.addWidget(header)

        # ================== Cards ==================
        # --- Game Optimization Tools ---
        tools = Card("Game Optimization Tools")
        tl = tools.body()

        self.btn_optimize = QPushButton("Apply Default Game Optimizations")
        self.btn_revert = QPushButton("Revert Optimizations")
        tl.addWidget(self.btn_optimize)
        tl.addWidget(self.btn_revert)

        # --- Custom Profile Loader ---
        profiles = Card("Custom Game Profiles")
        pv = profiles.body()

        self.btn_load_profile = QPushButton("Load Custom Profile (.json)")
        self.btn_apply_profile = QPushButton("Apply Loaded Profile")
        self.profile_info = QTextEdit()
        self.profile_info.setReadOnly(True)
        self.profile_info.setFixedHeight(150)
        self.profile_info.setStyleSheet("background: rgba(255,255,255,0.05); color:#DDD; font-size:10pt;")

        pv.addWidget(self.btn_load_profile)
        pv.addWidget(self.btn_apply_profile)
        pv.addWidget(self.profile_info)

        # --- Log Output ---
        logs = Card("Log Output")
        lv = logs.body()
        self.log = QTextEdit()
        self.log.setReadOnly(True)
        lv.addWidget(self.log)

        # Add to root
        root.addWidget(tools)
        root.addWidget(profiles)
        root.addWidget(logs)
        root.addStretch()

        # Animations
        for w in (tools, profiles, logs):
            fade_in(w)
            slide_in_y(w)

        # Signals
        self.btn_optimize.clicked.connect(self._apply_default)
        self.btn_revert.clicked.connect(self._revert_default)
        self.btn_load_profile.clicked.connect(self._load_profile)
        self.btn_apply_profile.clicked.connect(self._apply_profile)

    # ================== Actions ==================
    def _apply_default(self):
        msg = self.opt.apply_default_game_tweaks()
        self.log.append(f"[Game Optimizer] {msg}")

    def _revert_default(self):
        msg = self.opt.revert_default_game_tweaks()
        self.log.append(f"[Revert] {msg}")

    def _load_profile(self):
        """Open a JSON file and preview its contents."""
        path, _ = QFileDialog.getOpenFileName(self, "Select Game Profile", str(Path.cwd() / "profiles"), "JSON Files (*.json)")
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.loaded_profile = data
            self.loaded_path = path
            name = data.get("name", "Unnamed Profile")
            desc = data.get("description", "No description.")
            tweaks = data.get("tweaks", {})
            self.profile_info.setText(f"Name: {name}\n\nDescription: {desc}\n\nTweaks: {len(tweaks)} items\nPath: {path}")
            self.log.append(f"[Profile] Loaded {name} ({len(tweaks)} tweaks)")
        except Exception as e:
            self.profile_info.setText(f"Failed to load profile: {e}")
            self.log.append(f"[Error] Failed to load profile: {e}")

    def _apply_profile(self):
        """Apply tweaks from the loaded JSON profile."""
        if not self.loaded_profile:
            self.log.append("[Error] No profile loaded.")
            return
        try:
            msg = self.opt.apply_profile(self.loaded_profile)
            self.log.append(f"[Profile] {msg}")
        except Exception as e:
            self.log.append(f"[Error] Failed to apply profile: {e}")
