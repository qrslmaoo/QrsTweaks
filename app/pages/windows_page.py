from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QTextEdit, QHBoxLayout, QMessageBox
from src.qrs.modules.windows_optim import WindowsOptimizer
from app.ui.widgets.card import Card
from app.ui.widgets.toggle import Toggle

class WindowsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.opt = WindowsOptimizer()

        root = QVBoxLayout(self); root.setContentsMargins(4,4,4,4); root.setSpacing(10)

        scan = Card("System Scan")
        sv = scan.body()
        self.out = QTextEdit(); self.out.setReadOnly(True)
        btn = QPushButton("Run Quick Scan")
        btn.clicked.connect(self._scan)
        sv.addWidget(btn); sv.addWidget(self.out)
        root.addWidget(scan)

        row = QHBoxLayout()
        power = Card("Power Plan")
        pv = power.body()
        self.turbo = Toggle(on_text="On", off_text="Off")
        bpower = QPushButton("Create High Performance plan")
        bpower.clicked.connect(self._power)
        pv.addWidget(self.turbo); pv.addWidget(bpower)
        row.addWidget(power)

        clean = Card("Cleanup")
        cv = clean.body()
        bclean = QPushButton("Clean Temp Files")
        bclean.clicked.connect(self._clean)
        cv.addWidget(bclean)
        row.addWidget(clean)

        restore = Card("Safety")
        rv = restore.body()
        bres = QPushButton("Create Restore Point")
        bres.clicked.connect(self._restore)
        rv.addWidget(bres)
        row.addWidget(restore)

        root.addLayout(row)
        root.addStretch()

    def _scan(self):
        self.out.setPlainText(self.opt.quick_scan())

    def _power(self):
        ok, msg = self.opt.create_high_perf_powerplan()
        QMessageBox.information(self, "Power Plan", msg if ok else f"Failed: {msg}")

    def _clean(self):
        n = self.opt.cleanup_temp_files()
        QMessageBox.information(self, "Cleanup", f"Removed ~{n} temp files.")

    def _restore(self):
        ok, msg = self.opt.create_restore_point("QrsTweaks Snapshot")
        QMessageBox.information(self, "Restore Point", msg if ok else f"Failed: {msg}")
