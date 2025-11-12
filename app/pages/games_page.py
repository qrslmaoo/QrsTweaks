from PySide6.QtWidgets import QWidget, QVBoxLayout, QScrollArea, QPushButton, QLabel, QTextEdit
from PySide6.QtCore import Qt
from app.ui.widgets.card import Card
from src.qrs.modules.game_optim import GameOptimizer


class GamesPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background: transparent;")
        self.opt = GameOptimizer("profiles/")

        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        inner = QWidget()
        layout = QVBoxLayout(inner)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(12)

        header = QLabel("Game Optimizer")
        header.setStyleSheet("color:#DDE1EA; font-size:20pt; font-weight:700;")
        layout.addWidget(header)

        # Profile selection
        card_profiles = Card("Select Optimization Profile")
        body = card_profiles.body()
        for name in ["Fortnite Profile", "Minecraft Profile", "Load Custom Profile"]:
            btn = QPushButton(name)
            body.addWidget(btn)
        layout.addWidget(card_profiles)

        # Performance tweaks
        card_perf = Card("Performance Tweaks")
        body2 = card_perf.body()
        for name in ["Run FPS Stabilizer", "Optimize Latency", "Clear Shader Cache", "GPU Power Mode: Max Performance"]:
            btn = QPushButton(name)
            body2.addWidget(btn)
        layout.addWidget(card_perf)

        # Log
        card_log = Card("Game Optimizer Log")
        body3 = card_log.body()
        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setMinimumHeight(180)
        body3.addWidget(self.log)
        layout.addWidget(card_log)
        layout.addStretch()

        scroll.setWidget(inner)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)
