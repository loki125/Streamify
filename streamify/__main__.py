import sys

from PyQt6.QtCore.QtWidgets import QApplication

from .ui.main_window import MainWindow
from .ui.utils.config import load_stylesheet

if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Load your dark.css!
    load_stylesheet(app, theme_name="dark")

    window = MainWindow()
    window.show()
    sys.exit(app.exec())
