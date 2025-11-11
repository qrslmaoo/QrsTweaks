import json
import os
import sys
from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon, QAction
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QTabWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFileDialog, QMessageBox, QLineEdit, QTextEdit,
    QGroupBox, QFormLayout, QListWidget, QListWidgetItem, QStatusBar
)

# Local imports (add repo root to sys.path)
ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))

from qrs.core.paths import ensure_app_dirs, data_dir, config_dir
from qrs.modules.windows_optim import WindowsOptimizer
from qrs.modules.game_optim import GameOptimizer
from qrs.modules.passwords.vault import Vault, VaultError


class WindowsTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.opt = WindowsOptimizer()
        layout = QVBoxLayout(self)

        grp_scan = QGroupBox("System Scan (offline heuristics)")
        f1 = QVBoxLayout()
        self.scan_output = QTextEdit()
        self.scan_output.setReadOnly(True)
        btn_scan = QPushButton("Run Quick Scan")
        btn_scan.clicked.connect(self.run_scan)
        f1.addWidget(btn_scan)
        f1.addWidget(self.scan_output)
        grp_scan.setLayout(f1)

        grp_actions = QGroupBox("One-click Optimizations")
        f2 = QHBoxLayout()
        btn_power = QPushButton("Create High Performance plan")
        btn_power.clicked.connect(self.create_power)
        btn_cleanup = QPushButton("Clean Temp Files")
        btn_cleanup.clicked.connect(self.cleanup_temp)
        btn_restore = QPushButton("Create Restore Point")
        btn_restore.clicked.connect(self.restore_point)
        f2.addWidget(btn_power)
        f2.addWidget(btn_cleanup)
        f2.addWidget(btn_restore)
        grp_actions.setLayout(f2)

        layout.addWidget(grp_scan)
        layout.addWidget(grp_actions)
        layout.addStretch()

    def run_scan(self):
        report = self.opt.quick_scan()
        self.scan_output.setPlainText(report)

    def create_power(self):
        ok, msg = self.opt.create_high_perf_powerplan()
        QMessageBox.information(self, "Power Plan", msg if ok else f"Failed: {msg}")

    def cleanup_temp(self):
        count = self.opt.cleanup_temp_files()
        QMessageBox.information(self, "Cleanup", f"Removed ~{count} temp files.")

    def restore_point(self):
        ok, msg = self.opt.create_restore_point("QrsTweaks Snapshot")
        QMessageBox.information(self, "Restore Point", msg if ok else f"Failed: {msg}")


class GamesTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.game = GameOptimizer(profiles_dir=ROOT / "assets" / "profiles")

        layout = QHBoxLayout(self)
        self.list_profiles = QListWidget()
        for name in self.game.list_profiles():
            QListWidgetItem(name, self.list_profiles)

        right = QVBoxLayout()
        self.txt_preview = QTextEdit()
        self.txt_preview.setReadOnly(True)
        btn_apply = QPushButton("Apply Profile")
        btn_apply.clicked.connect(self.apply_selected)
        btn_open = QPushButton("Open Profiles Folder")
        btn_open.clicked.connect(self.open_profiles)

        right.addWidget(QLabel("Profile Preview"))
        right.addWidget(self.txt_preview)
        right.addWidget(btn_apply)
        right.addWidget(btn_open)
        right.addStretch()

        self.list_profiles.currentItemChanged.connect(self.on_select)
        layout.addWidget(self.list_profiles, 1)
        layout.addLayout(right, 2)

    def on_select(self, item: Optional[QListWidgetItem]):
        if not item:
            self.txt_preview.clear()
            return
        data = self.game.load_profile(item.text())
        self.txt_preview.setPlainText(json.dumps(data, indent=2))

    def apply_selected(self):
        item = self.list_profiles.currentItem()
        if not item:
            return
        name = item.text()
        ok, msg = self.game.apply_profile(name)
        QMessageBox.information(self, "Apply Profile", msg if ok else f"Failed: {msg}")

    def open_profiles(self):
        os.startfile(self.game.profiles_dir)  # Windows-only convenience


class PasswordsTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        ensure_app_dirs()
        self.vault_path = data_dir() / "vault.qrsvault"
        self.vault = Vault(self.vault_path)

        layout = QVBoxLayout(self)

        grp_unlock = QGroupBox("Unlock / Create Vault")
        f0 = QFormLayout()
        self.edit_pass = QLineEdit()
        self.edit_pass.setEchoMode(QLineEdit.Password)
        btn_unlock = QPushButton("Unlock or Create")
        btn_unlock.clicked.connect(self.unlock_or_create)
        f0.addRow("Master Password:", self.edit_pass)
        f0.addRow(btn_unlock)
        grp_unlock.setLayout(f0)

        grp_entry = QGroupBox("Add Entry")
        f1 = QFormLayout()
        self.e_title = QLineEdit()
        self.e_user = QLineEdit()
        self.e_secret = QLineEdit()
        self.e_secret.setEchoMode(QLineEdit.Password)
        btn_add = QPushButton("Add")
        btn_add.clicked.connect(self.add_entry)
        f1.addRow("Title:", self.e_title)
        f1.addRow("Username:", self.e_user)
        f1.addRow("Password:", self.e_secret)
        f1.addRow(btn_add)
        grp_entry.setLayout(f1)

        grp_list = QGroupBox("Entries (Local Only)")
        v2 = QVBoxLayout()
        self.list_entries = QListWidget()
        btn_export = QPushButton("Export Decrypted (to CSV)")
        btn_export.clicked.connect(self.export_csv)
        v2.addWidget(self.list_entries)
        v2.addWidget(btn_export)
        grp_list.setLayout(v2)

        layout.addWidget(grp_unlock)
        layout.addWidget(grp_entry)
        layout.addWidget(grp_list)
        layout.addStretch()

        self.setEnabled(False)  # disabled until unlocked

    def unlock_or_create(self):
        pwd = self.edit_pass.text()
        if not pwd:
            QMessageBox.warning(self, "Vault", "Enter a master password.")
            return
        try:
            created = self.vault.unlock_or_create(pwd)
        except VaultError as e:
            QMessageBox.critical(self, "Vault", str(e))
            return
        self.setEnabled(True)
        self.refresh_list()
        QMessageBox.information(self, "Vault", "Vault created." if created else "Vault unlocked.")

    def add_entry(self):
        try:
            self.vault.add_entry(
                title=self.e_title.text().strip(),
                username=self.e_user.text().strip(),
                password=self.e_secret.text().strip(),
            )
            self.vault.save()
            self.refresh_list()
            self.e_title.clear(); self.e_user.clear(); self.e_secret.clear()
        except VaultError as e:
            QMessageBox.critical(self, "Vault", str(e))

    def refresh_list(self):
        self.list_entries.clear()
        for it in self.vault.list_entries():
            QListWidgetItem(f"{it['title']}  —  {it['username']}", self.list_entries)

    def export_csv(self):
        if not self.vault.is_open:
            QMessageBox.warning(self, "Vault", "Unlock first.")
            return
        path, _ = QFileDialog.getSaveFileName(self, "Export CSV", str(data_dir() / "vault_export.csv"), "CSV (*.csv)")
        if not path:
            return
        try:
            count = self.vault.export_csv(Path(path))
            QMessageBox.information(self, "Export", f"Exported {count} entries to {path}")
        except VaultError as e:
            QMessageBox.critical(self, "Export", str(e))


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("QrsTweaks — Local Suite")
        self.resize(1120, 720)
        self.setWindowIcon(QIcon())

        # Tabs
        tabs = QTabWidget()
        tabs.addTab(WindowsTab(), "Windows Optimizer")
        tabs.addTab(GamesTab(), "Game Optimizer")
        tabs.addTab(PasswordsTab(), "Password Manager")
        self.setCentralWidget(tabs)

        # Menu
        menubar = self.menuBar()
        file_menu = menubar.addMenu("&File")
        act_open_profiles = QAction("Open Profiles Folder", self)
        act_open_profiles.triggered.connect(lambda: os.startfile((ROOT / "assets" / "profiles")))
        file_menu.addAction(act_open_profiles)

        theme_menu = menubar.addMenu("&Theme")
        act_dark = QAction("Dark", self)
        act_dark.triggered.connect(lambda: self.apply_theme("dark"))
        act_light = QAction("Light (reset)", self)
        act_light.triggered.connect(lambda: self.apply_theme("light"))
        theme_menu.addAction(act_dark); theme_menu.addAction(act_light)

        # Status
        self.status = QStatusBar()
        self.setStatusBar(self.status)
        self.apply_theme("dark")

    def apply_theme(self, name: str):
        if name == "dark":
            qss_path = ROOT / "app" / "qdark.qss"
            self.status.showMessage("Theme: Dark", 2000)
            if qss_path.exists():
                with open(qss_path, "r", encoding="utf-8") as fh:
                    self.setStyleSheet(fh.read())
        else:
            self.setStyleSheet("")
            self.status.showMessage("Theme: Light", 2000)


def main():
    ensure_app_dirs()
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())
    

if __name__ == "__main__":
    main()
