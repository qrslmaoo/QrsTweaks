from pathlib import Path
from PySide6.QtWidgets import QWidget, QVBoxLayout, QFormLayout, QLineEdit, QPushButton, QListWidget, QListWidgetItem, QFileDialog, QMessageBox
from src.qrs.core.paths import data_dir, ensure_app_dirs
from src.qrs.modules.passwords.vault import Vault, VaultError
from app.ui.widgets.card import Card

class PasswordsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        ensure_app_dirs()
        self.vault_path = data_dir() / "vault.qrsvault"
        self.vault = Vault(self.vault_path)

        root = QVBoxLayout(self); root.setContentsMargins(4,4,4,4); root.setSpacing(10)

        unlock = Card("Unlock / Create Vault")
        f = QFormLayout()
        self.e_pass = QLineEdit(); self.e_pass.setEchoMode(QLineEdit.Password)
        b = QPushButton("Unlock or Create")
        b.clicked.connect(self._unlock)
        f.addRow("Master Password:", self.e_pass); f.addRow(b)
        unlock.body().addLayout(f)
        root.addWidget(unlock)

        add = Card("Add Entry")
        f2 = QFormLayout()
        self.t = QLineEdit(); self.u = QLineEdit(); self.p = QLineEdit(); self.p.setEchoMode(QLineEdit.Password)
        b2 = QPushButton("Add"); b2.clicked.connect(self._add)
        f2.addRow("Title:", self.t); f2.addRow("Username:", self.u); f2.addRow("Password:", self.p); f2.addRow(b2)
        add.body().addLayout(f2)
        root.addWidget(add)

        listc = Card("Entries")
        self.listw = QListWidget()
        b3 = QPushButton("Export to CSV"); b3.clicked.connect(self._export)
        listc.body().addWidget(self.listw); listc.body().addWidget(b3)
        root.addWidget(listc, 1)

        self.setEnabled(False)

    def _unlock(self):
        try:
            created = self.vault.unlock_or_create(self.e_pass.text())
            self.setEnabled(True); self._refresh()
            QMessageBox.information(self, "Vault", "Vault created." if created else "Vault unlocked.")
        except VaultError as e:
            QMessageBox.critical(self, "Vault", str(e))

    def _add(self):
        try:
            self.vault.add_entry(self.t.text().strip(), self.u.text().strip(), self.p.text().strip())
            self.vault.save(); self._refresh()
            self.t.clear(); self.u.clear(); self.p.clear()
        except VaultError as e:
            QMessageBox.critical(self, "Vault", str(e))

    def _refresh(self):
        self.listw.clear()
        for it in self.vault.list_entries():
            QListWidgetItem(f"{it['title']} — {it['username']}", self.listw)

    def _export(self):
        if not self.vault.is_open: 
            QMessageBox.warning(self, "Vault", "Unlock first."); return
        path, _ = QFileDialog.getSaveFileName(self, "Export CSV", str(data_dir() / "vault_export.csv"), "CSV (*.csv)")
        if not path: return
        try:
            n = self.vault.export_csv(Path(path))
            QMessageBox.information(self, "Export", f"Exported {n} entries.")
        except VaultError as e:
            QMessageBox.critical(self, "Export", str(e))
