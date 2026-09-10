import sys
from locale import LC_NUMERIC, setlocale

from PyQt6.QtWidgets import QApplication

from .backend.manager import StreamlinkManager
from .ui.main_window import MainWindow

# from .ui.utils.config import load_stylesheet
# emojies : ⟳ ✚ ⌨ ⚙️ ☾☼ ✏️ ✍︎ ⇄ ▶︎ ☰ ☕︎ ✘ ➜] ✖
LOCALE_C = "C"


def main() -> None:
    app = QApplication(sys.argv)
    # load_stylesheet(app, theme_name="dark")
    _ = setlocale(LC_NUMERIC, LOCALE_C)

    with StreamlinkManager() as manager:
        window = MainWindow(manager)
        window.show()

        exit_code = app.exec()

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
