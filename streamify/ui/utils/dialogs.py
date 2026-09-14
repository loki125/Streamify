# pyright: reportUnknownMemberType=none
from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QKeySequence
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QInputDialog,
    QKeySequenceEdit,
    QLineEdit,
    QPushButton,
    QSlider,
    QToolButton,
    QWidget,
)

from streamify.backend.core.models import CustomSettings, Quality, Settings, Stream
from streamify.backend.manager import StreamlinkManager

from ..utils.config import TWITCH_IMPORT_HELP


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


class TwitchImportDialog(QDialog):
    """Dialog for entering Twitch API credentials."""

    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)
        self.setWindowTitle("Import Twitch Follows")
        self.resize(350, 150)

        layout = QFormLayout(self)
        self.client_id_input: QLineEdit = QLineEdit()
        self.access_token_input: QLineEdit = QLineEdit()
        self.access_token_input.setEchoMode(QLineEdit.EchoMode.Password)

        layout.addRow("Client ID:", self.client_id_input)
        layout.addRow("Access Token:", self.access_token_input)

        bottom_layout = QHBoxLayout()

        help_btn = QToolButton()
        help_btn.setText("?")
        _ = help_btn.setToolTip(TWITCH_IMPORT_HELP)

        self.buttons: QDialogButtonBox = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        _ = self.buttons.accepted.connect(self.accept)
        _ = self.buttons.rejected.connect(self.reject)

        bottom_layout.addWidget(help_btn)
        bottom_layout.addStretch()
        bottom_layout.addWidget(self.buttons)

        layout.addRow(bottom_layout)

    def get_credentials(self) -> tuple[str, str]:
        return (
            self.client_id_input.text().strip(),
            self.access_token_input.text().strip(),
        )


class CustomStreamSettingsDialog(QDialog):
    """Dialog for stream-specific overrides with a Reset to Defaults button."""

    def __init__(
        self,
        parent: QWidget,
        current_custom: CustomSettings | None,
        global_defaults: Settings,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Custom Stream Settings")
        self.setFixedWidth(340)

        self.global_defaults: Settings = global_defaults
        self.settings: CustomSettings = (
            current_custom
            if current_custom
            else CustomSettings.default(global_defaults)
        )

        self.is_reset_to_default: bool = False

        layout = QFormLayout(self)

        self.chat_check: QCheckBox = QCheckBox()
        self.chat_check.setChecked(self.settings.chat_active)

        self.pause_input: QKeySequenceEdit = QKeySequenceEdit(
            self.settings.pause_start_key
        )
        self.mute_input: QKeySequenceEdit = QKeySequenceEdit(
            self.settings.mute_unmute_key
        )

        self.vol_slider: QSlider = QSlider(Qt.Orientation.Horizontal)
        self.vol_slider.setRange(0, 100)
        self.vol_slider.setValue(self.settings.volume_num)

        layout.addRow("Chat Active (Future):", self.chat_check)
        layout.addRow("Pause/Start Key:", self.pause_input)
        layout.addRow("Mute/Unmute Key:", self.mute_input)
        layout.addRow("Stream Volume (0-100):", self.vol_slider)

        bottom_bar = QHBoxLayout()

        self.btn_reset: QPushButton = QPushButton("⇄ Revert")
        self.btn_reset.setToolTip("Revert to global settings")
        self.btn_reset.setStyleSheet("color: white;")
        _ = self.btn_reset.clicked.connect(self.reset_to_defaults)

        self.buttons: QDialogButtonBox = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        _ = self.buttons.accepted.connect(self.accept)
        _ = self.buttons.rejected.connect(self.reject)

        bottom_bar.addWidget(self.btn_reset)
        bottom_bar.addStretch()
        bottom_bar.addWidget(self.buttons)

        layout.addRow(bottom_bar)

        _ = self.chat_check.toggled.connect(self._mark_custom)
        _ = self.pause_input.keySequenceChanged.connect(self._mark_custom)
        _ = self.mute_input.keySequenceChanged.connect(self._mark_custom)
        _ = self.vol_slider.valueChanged.connect(self._mark_custom)

    def _mark_custom(self) -> None:
        self.is_reset_to_default = False

    def reset_to_defaults(self) -> None:
        """Repopulates all fields with the global settings values."""
        self.is_reset_to_default = True
        self.chat_check.setChecked(self.global_defaults.default_chat_active)
        self.pause_input.setKeySequence(
            QKeySequence(self.global_defaults.default_pause_start_key)
        )
        self.mute_input.setKeySequence(
            QKeySequence(self.global_defaults.default_mute_unmute_key)
        )
        self.vol_slider.setValue(self.global_defaults.default_volume_num)

    def get_custom_settings(self) -> CustomSettings:
        return CustomSettings(
            chat_active=self.chat_check.isChecked(),
            pause_start_key=self.pause_input.keySequence().toString(),
            mute_unmute_key=self.mute_input.keySequence().toString(),
            volume_num=self.vol_slider.value(),
        )
