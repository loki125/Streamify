import sys

from PyQt6.QtWidgets import QApplication

from .ui.main_window import MainWindow
from .ui.utils.config import load_stylesheet


def main() -> None:
    app = QApplication(sys.argv)

    load_stylesheet(app, theme_name="dark")

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
