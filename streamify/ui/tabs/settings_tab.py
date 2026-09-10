# pyright: reportUnknownMemberType=none
from __future__ import annotations

from typing import Any

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from streamify.backend.core.models import Quality, Settings, Theme
from streamify.backend.fetcher_factory import FetcherFactory
from streamify.backend.manager import StreamlinkManager
from streamify.backend.settings import SettingsConfig

from ..utils import dialogs
from ..utils.config import JSON_EDIT_NOTE, JSON_EDIT_WARNING, load_stylesheet
from ..utils.signals import FetchFollowsWorker, safe_connect


class SettingsTab(QWidget):
    def __init__(
        self,
        manager: StreamlinkManager,
        settings_config: SettingsConfig,
        main_window: QWidget,
    ) -> None:
        super().__init__()
        self.manager: StreamlinkManager = manager
        self.settings_config: SettingsConfig = settings_config
        self.main_window: QWidget = main_window
        self.settings: Settings = self.settings_config.get_settings()

        self.init_ui()

    def init_ui(self) -> None:
        main_layout = QVBoxLayout(self)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_content = QWidget()
        form_layout = QFormLayout(scroll_content)

        self.auto_quality_check: QCheckBox = QCheckBox("Enable Auto-Select Quality")
        self.auto_quality_check.setChecked(self.settings.auto_select_quality[1])

        self.quality_combo: QComboBox = QComboBox()
        self.quality_combo.addItems([q.value for q in Quality])
        self.quality_combo.setCurrentText(self.settings.auto_select_quality[0].value)

        self.chat_check: QCheckBox = QCheckBox("Default Chat Active (Future)")
        self.chat_check.setChecked(self.settings.default_chat_active)

        self.pause_input: QLineEdit = QLineEdit(self.settings.default_pause_start_key)
        self.mute_input: QLineEdit = QLineEdit(self.settings.default_mute_unmute_key)

        self.refresh_spin: QDoubleSpinBox = QDoubleSpinBox()
        self.refresh_spin.setRange(10.0, 3600.0)
        self.refresh_spin.setSuffix(" seconds")
        self.refresh_spin.setValue(self.settings.auto_refresh_sec)

        self.theme_combo: QComboBox = QComboBox()
        self.theme_combo.addItems([t.value for t in Theme])
        self.theme_combo.setCurrentText(self.settings.dark_light_mode.value)

        self.vol_slider: QSlider = QSlider(Qt.Orientation.Horizontal)
        self.vol_slider.setRange(0, 100)
        self.vol_slider.setValue(self.settings.default_volume_num)

        form_layout.addRow(self.auto_quality_check, self.quality_combo)
        form_layout.addRow("Default Pause/Start Key:", self.pause_input)
        form_layout.addRow("Default Mute/Unmute Key:", self.mute_input)
        form_layout.addRow("Default Chat:", self.chat_check)
        form_layout.addRow("Auto Refresh Rate:", self.refresh_spin)
        form_layout.addRow("Theme:", self.theme_combo)
        form_layout.addRow("Volume (0-100):", self.vol_slider)

        scroll_area.setWidget(scroll_content)
        main_layout.addWidget(scroll_area)

        # ================== ACTION BUTTONS ==================
        btn_layout = QHBoxLayout()

        self.btn_save: QPushButton = QPushButton("Save Settings")
        safe_connect(self.btn_save.clicked, self.save_settings)

        self.btn_twitch: QPushButton = QPushButton("Import Twitch Follows")
        safe_connect(self.btn_twitch.clicked, self.open_twitch_dialog)

        self.btn_edit_json: QPushButton = QPushButton("Edit streamify.json")
        safe_connect(self.btn_edit_json.clicked, self.edit_json)

        self.btn_reset: QPushButton = QPushButton("RESET Stream List")
        self.btn_reset.setStyleSheet(
            "background-color: darkred; color: white; font-weight: bold;"
        )
        safe_connect(self.btn_reset.clicked, self.reset_streams)

        btn_layout.addWidget(self.btn_save)
        btn_layout.addWidget(self.btn_twitch)
        btn_layout.addWidget(self.btn_edit_json)
        btn_layout.addWidget(self.btn_reset)

        main_layout.addLayout(btn_layout)

    def save_settings(self) -> None:
        self.settings.auto_select_quality = (
            Quality(self.quality_combo.currentText()),
            self.auto_quality_check.isChecked(),
        )
        self.settings.default_pause_start_key = self.pause_input.text()
        self.settings.default_mute_unmute_key = self.mute_input.text()
        self.settings.default_chat_active = self.chat_check.isChecked()
        self.settings.auto_refresh_sec = self.refresh_spin.value()
        self.settings.default_volume_num = self.vol_slider.value()

        self.set_theme()

        self.settings_config.save_settings(self.settings)
        _ = QMessageBox.information(self, "Success", "Settings saved successfully.")

    def set_theme(self) -> None:
        new_theme = Theme(self.theme_combo.currentText())
        if self.settings.dark_light_mode != new_theme:
            self.settings.dark_light_mode = new_theme

        if self.settings.dark_light_mode != new_theme:
            self.settings.dark_light_mode = new_theme

            app = QApplication.instance()

            if isinstance(app, QApplication):
                load_stylesheet(app, theme_name=new_theme.value)

    def open_twitch_dialog(self) -> None:
        dialog = dialogs.TwitchImportDialog(self)
        if dialog.exec():
            client_id, access_token = dialog.get_credentials()
            if client_id and access_token:
                self.btn_twitch.setEnabled(False)
                self.btn_twitch.setText("Fetching...")

                twitch_worker = FetchFollowsWorker(
                    FetcherFactory().get_fetcher(
                        "twitch", client_id=client_id, access_token=access_token
                    )
                )

                def on_success(streams: list[Any]) -> None:
                    for s in streams:
                        _ = self.manager.add_stream(s.name, s.url, s.category_id)
                    _ = QMessageBox.information(
                        self, "Success", f"Imported {len(streams)} streams."
                    )
                    self.btn_twitch.setEnabled(True)
                    self.btn_twitch.setText("Import Twitch Follows")

                def on_error(err: str) -> None:
                    _ = QMessageBox.warning(self, "Error", f"Failed: {err}")
                    self.btn_twitch.setEnabled(True)
                    self.btn_twitch.setText("Import Twitch Follows")

                safe_connect(twitch_worker.finished, on_success)
                safe_connect(twitch_worker.error, on_error)
                twitch_worker.start()

    def edit_json(self) -> None:
        reply = QMessageBox.question(
            self,
            "Edit Database",
            JSON_EDIT_WARNING,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                pass  # TODO: Open JSON editor
            except (FileNotFoundError, PermissionError) as e:
                _ = QMessageBox.warning(self, "Error", f"Could not open editor: {e}")

    def reset_streams(self) -> None:
        msg = "This will delete ALL streams from your app. Are you absolutely sure?"
        reply = QMessageBox.critical(
            self,
            "RESET",
            msg,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.manager.remove_all_streams()

            _ = QMessageBox.information(
                self,
                "Reset Complete",
                JSON_EDIT_NOTE,
            )
