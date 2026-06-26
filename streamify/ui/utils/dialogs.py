from PyQt5.QtWidgets import QComboBox, QDialog, QFormLayout, QLineEdit, QPushButton


class AddStreamDialog(QDialog):
    def __init__(self, manager, parent=None):
        super().__init__(parent)
        self.manager = manager
        self.setWindowTitle("Add New Stream")
        self.resize(320, 160)

        layout = QFormLayout(self)
        layout.setSpacing(12)

        self.name_input = QLineEdit()
        layout.addRow("Stream Name (Channel):", self.name_input)

        self.url_cb = QComboBox()
        self.url_cb.addItems(list(self.manager.urls.keys()))
        layout.addRow("Platform (URL):", self.url_cb)

        self.cat_cb = QComboBox()
        self.cat_cb.addItems(list(self.manager.categorys.keys()))
        layout.addRow("Category:", self.cat_cb)

        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.accept)
        layout.addRow("", save_btn)

    def get_data(self):
        return (
            self.name_input.text().strip(),
            self.url_cb.currentText(),
            self.cat_cb.currentText(),
        )
