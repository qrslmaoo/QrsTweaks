from PySide6.QtWidgets import QWidget, QVBoxLayout, QScrollArea, QPushButton, QLabel, QTextEdit
from PySide6.QtCore import Qt
from app.ui.widgets.card import Card
from src.qrs.modules.passwords.vault import PasswordVault


class PasswordsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background: transparent;")
        self.vault = PasswordVault()

        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        inner = QWidget()
        layout = QVBoxLayout(inner)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(12)

        header = QLabel("Password Manager")
        header.setStyleSheet("color:#DDE1EA; font-size:20pt; font-weight:700;")
        layout.addWidget(header)

        card_vault = Card("Unlock / Create Vault")
        body = card_vault.body()
        btn_unlock = QPushButton("Unlock / Create Vault")
        body.addWidget(btn_unlock)
        layout.addWidget(card_vault)

        card_add = Card("Add Entry")
        body2 = card_add.body()
        btn_add = QPushButton("Add Entry")
        body2.addWidget(btn_add)
        layout.addWidget(card_add)

        card_entries = Card("Entries")
        body3 = card_entries.body()
        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setMinimumHeight(200)
        body3.addWidget(self.log)
        layout.addWidget(card_entries)
        layout.addStretch()

        scroll.setWidget(inner)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)
