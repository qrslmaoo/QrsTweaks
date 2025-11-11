# app/pages/passwords_page.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QLineEdit, QHBoxLayout, QListWidget
)
from PySide6.QtCore import Qt

from app.ui.widgets.card import Card
from app.ui.animations import fade_in, slide_in_y
from src.qrs.modules.passwords.vault import PasswordVault


class PasswordsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.vault = PasswordVault()

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(18)

        header = QLabel("Password Manager")
        header.setStyleSheet("color:#DDE1EA; font-size:22pt; font-weight:700;")
        header.setAlignment(Qt.AlignLeft)
        root.addWidget(header)

        # -------------- Unlock/Create --------------
        vault_card = Card("Unlock / Create Vault")
        vv = vault_card.body()

        self.entry_pass = QLineEdit()
        self.entry_pass.setEchoMode(QLineEdit.Password)

        self.btn_unlock = QPushButton("Unlock / Create")
        vv.addWidget(self.entry_pass)
        vv.addWidget(self.btn_unlock)

        root.addWidget(vault_card)

        # -------------- Add Entry --------------
        add = Card("Add Entry")
        av = add.body()

        self.site = QLineEdit(); self.site.setPlaceholderText("Site")
        self.user = QLineEdit(); self.user.setPlaceholderText("Username")
        self.pwd = QLineEdit(); self.pwd.setPlaceholderText("Password")

        self.btn_add = QPushButton("Add")

        av.addWidget(self.site)
        av.addWidget(self.user)
        av.addWidget(self.pwd)
        av.addWidget(self.btn_add)

        root.addWidget(add)

        # -------------- List Entries --------------
        lst = Card("Entries")
        lv = lst.body()

        self.list_entries = QListWidget()
        lv.addWidget(self.list_entries)

        root.addWidget(lst)
        root.addStretch()

        # Signals
        self.btn_unlock.clicked.connect(self._unlock)
        self.btn_add.clicked.connect(self._add)

        # Animations
        for card in (vault_card, add, lst):
            fade_in(card)
            slide_in_y(card)

    def _unlock(self):
        pwd = self.entry_pass.text().strip()
        self.vault.unlock(pwd)
        self._refresh()

    def _add(self):
        self.vault.add(
            self.site.text(),
            self.user.text(),
            self.pwd.text(),
        )
        self.site.clear()
        self.user.clear()
        self.pwd.clear()
        self._refresh()

    def _refresh(self):
        self.list_entries.clear()
        for s, u, p in self.vault.list_all():
            self.list_entries.addItem(f"{s} | {u} | {p}")
