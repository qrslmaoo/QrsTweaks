import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

QSS_PATH = ROOT / "app" / "qdark.qss"


from app.ui.suite_window import SuiteWindow
from app.pages.windows_page import WindowsPage
from app.pages.games_page import GamesPage
from app.pages.passwords_page import PasswordsPage


def main():
    app = QApplication(sys.argv)

    # Apply theme AFTER the app is created
    if QSS_PATH.exists():
        app.setStyleSheet(QSS_PATH.read_text(encoding="utf-8"))

    win_page = WindowsPage()
    game_page = GamesPage()
    pass_page = PasswordsPage()

    ui = SuiteWindow(win_page, game_page, pass_page)
    ui.resize(1280, 780)
    ui.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
