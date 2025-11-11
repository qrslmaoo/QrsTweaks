import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.ui.suite_window import SuiteWindow
from app.pages.windows_page import WindowsPage
from app.pages.games_page import GamesPage
from app.pages.passwords_page import PasswordsPage

QSS = ""  # (optional)

def main():
    app = QApplication(sys.argv)
    if QSS:
        app.setStyleSheet(QSS)

    win_page = WindowsPage()
    game_page = GamesPage()
    pass_page = PasswordsPage()

    ui = SuiteWindow(win_page, game_page, pass_page)
    ui.resize(1280, 780)
    ui.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
