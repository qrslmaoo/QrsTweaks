import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication

# ---------------------------------------------------
#  Project Root Setup
# ---------------------------------------------------
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# Optional QSS theme
QSS_PATH = ROOT / "app" / "qdark.qss"


def main():
    app = QApplication(sys.argv)

    # Load external stylesheet if present
    if QSS_PATH.exists():
        app.setStyleSheet(QSS_PATH.read_text(encoding="utf-8"))

    # Import after QApplication (PySide6 requirement)
    from app.ui.suite_window import SuiteWindow

    # Create the window (NEW: no constructor arguments)
    ui = SuiteWindow()
    ui.resize(1280, 780)
    ui.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
