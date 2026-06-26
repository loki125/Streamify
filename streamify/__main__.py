import sys

from PyQt5.QtWidgets import QApplication

from streamify.ui.main_window import StreamlinkGUI


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = StreamlinkGUI()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
