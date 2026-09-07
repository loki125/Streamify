from PyQt5.QtWidgets import QComboBox, QDialog, QFormLayout, QLineEdit, QPushButton


class AddStreamDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
