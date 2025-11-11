# app/pages/games_page.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout
)
from PySide6.QtCore import Qt

from app.ui.widgets.card import Card
from app.ui.animations import fade_in, slide_in_y
from src.qrs.modules.game_optim import GameOptimizer


class GamesPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.opt = GameOptimizer()

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(18)

        header = QLabel("Game Optimizer")
        header.setStyleSheet("color:#DDE1EA; font-size:22pt; font-weight:700;")
        header.setAlignment(Qt.AlignLeft)
        root.addWidget(header)

        # --------------- Game Cards ---------------
        row = QHBoxLayout()
        row.setSpacing(18)

        fort = Card("Fortnite Optimizer")
        fv = fort.body()

        self.btn_fps = QPushButton("Enable FPS Boost")
        self.btn_net = QPushButton("Low Latency Mode")
        self.btn_cfg = QPushButton("Apply Fortnite Config")

        fv.addWidget(self.btn_fps)
        fv.addWidget(self.btn_net)
        fv.addWidget(self.btn_cfg)

        mc = Card("Minecraft Optimizer")
        mv = mc.body()

        self.btn_mc_r = QPushButton("Reduce Lag (1.8–1.21)")
        self.btn_mc_opt = QPushButton("Apply Sodium/Lithium")

        mv.addWidget(self.btn_mc_r)
        mv.addWidget(self.btn_mc_opt)

        row.addWidget(fort)
        row.addWidget(mc)

        root.addLayout(row)
        root.addStretch()

        # Signals
        self.btn_fps.clicked.connect(lambda: self.opt.fortnite_fps_boost())
        self.btn_net.clicked.connect(lambda: self.opt.fortnite_net_tweak())
        self.btn_cfg.clicked.connect(lambda: self.opt.apply_fortnite_cfg())

        self.btn_mc_r.clicked.connect(lambda: self.opt.minecraft_reduce_lag())
        self.btn_mc_opt.clicked.connect(lambda: self.opt.minecraft_sodium_opt())

        # Animations
        for card in (fort, mc):
            fade_in(card)
            slide_in_y(card)
