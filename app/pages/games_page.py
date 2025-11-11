import json, os
from pathlib import Path
from PySide6.QtWidgets import QWidget, QHBoxLayout, QListWidget, QListWidgetItem, QVBoxLayout, QLabel, QTextEdit, QPushButton, QMessageBox
from src.qrs.modules.game_optim import GameOptimizer
from app.ui.widgets.card import Card

ROOT = Path(__file__).resolve().parents[2]

class GamesPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.game = GameOptimizer(profiles_dir=ROOT / "assets" / "profiles")

        root = QHBoxLayout(self); root.setContentsMargins(4,4,4,4); root.setSpacing(10)

        left_card = Card("Profiles")
        lv = QVBoxLayout(); left_card.setLayout(lv)  # override to simple container
        self.list_profiles = QListWidget()
        for n in self.game.list_profiles():
            QListWidgetItem(n, self.list_profiles)
        lv.addWidget(self.list_profiles)
        root.addWidget(left_card, 1)

        right_card = Card("Profile Details")
        rv = right_card.body()
        self.preview = QTextEdit(); self.preview.setReadOnly(True)
        b_apply = QPushButton("Apply Profile")
        b_open = QPushButton("Open Profiles Folder")
        b_apply.clicked.connect(self._apply)
        b_open.clicked.connect(lambda: os.startfile(self.game.profiles_dir))
        rv.addWidget(self.preview); rv.addWidget(b_apply); rv.addWidget(b_open)
        root.addWidget(right_card, 2)

        self.list_profiles.currentItemChanged.connect(self._select)

    def _select(self, item):
        if not item:
            self.preview.clear(); return
        data = self.game.load_profile(item.text())
        self.preview.setPlainText(json.dumps(data, indent=2))

    def _apply(self):
        it = self.list_profiles.currentItem()
        if not it: return
        ok, msg = self.game.apply_profile(it.text())
        QMessageBox.information(self, "Apply Profile", msg if ok else f"Failed: {msg}")
