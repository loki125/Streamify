# pyright: reportUnknownMemberType=none
from __future__ import annotations

from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QInputDialog,
    QLineEdit,
    QWidget,
)

from streamify.backend.core.models import Quality, Stream
from streamify.backend.manager import StreamlinkManager


def ask_quality_dialog(parent: QWidget, fetched_qualities: list[str]) -> Quality | None:
    """Prompts the user for stream quality, returning a Quality Enum."""

    valid_enum_values = [q.value for q in Quality]

    display_qualities = [q for q in fetched_qualities if q in valid_enum_values]

    if not display_qualities:
        display_qualities = [
            Quality.best.value,
            Quality.worst.value,
            Quality.audio_only.value,
        ]

    quality_str, ok = QInputDialog.getItem(
        parent, "Select Quality", "Available Qualities:", display_qualities, 0, False
    )

    if ok and quality_str:
        return Quality(quality_str)

    return None


class StreamEditDialog(QDialog):
    """Dialog for adding or editing a stream with category auto-completion."""

    def __init__(
        self, parent: QWidget, manager: StreamlinkManager, stream: Stream | None = None
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Edit Stream" if stream else "Add Stream")
        self.resize(300, 150)

        self.manager: StreamlinkManager = manager
        self.stream: Stream | None = stream

        layout = QFormLayout(self)

        self.name_input: QLineEdit = QLineEdit()
        self.url_input: QLineEdit = QLineEdit()

        self.category_input: QComboBox = QComboBox()
        self.category_input.setEditable(True)

        self.existing_categories: list[str] = self.manager.get_all_categories()
        self.category_input.addItems(self.existing_categories)

        if stream:
            self.name_input.setText(stream.name)
            self.url_input.setText(stream.url)
            if 0 <= stream.category_id < len(self.existing_categories):
                self.category_input.setCurrentText(
                    self.existing_categories[stream.category_id]
                )

        layout.addRow("Name:", self.name_input)
        layout.addRow("URL:", self.url_input)
        layout.addRow("Category:", self.category_input)

        self.buttons: QDialogButtonBox = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        _ = self.buttons.accepted.connect(self.accept)
        _ = self.buttons.rejected.connect(self.reject)
        layout.addWidget(self.buttons)

    def get_data(self) -> tuple[str, str, str]:
        """Returns (name, url, category_string)"""
        return (
            self.name_input.text().strip(),
            self.url_input.text().strip(),
            self.category_input.currentText().strip(),
        )
