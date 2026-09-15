# pyright: reportUnknownMemberType=none
from __future__ import annotations

from typing import Any

from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QHBoxLayout,
    QKeySequenceEdit,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSlider,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from streamify.backend.core.config import STREAM_LIST
from streamify.backend.core.models import Quality, Settings, Stream, Theme
from streamify.backend.fetcher_factory import FetcherFactory
from streamify.backend.fetchers.config import TWITCH_CLIENT_ID, TWITCH_REDIRECT_PORT
from streamify.backend.manager import StreamlinkManager

from ..utils.config import JSON_EDIT_NOTE, JSON_EDIT_WARNING, load_stylesheet
from ..utils.signals import FetchFollowsWorker, PlatformAuthWorker, safe_connect


class SettingsTab(QWidget):
    def __init__(
        self,
        manager: StreamlinkManager,
        main_window: QWidget,
    ) -> None:
        super().__init__()
        self.manager: StreamlinkManager = manager
        self.main_window: QWidget = main_window
        self.settings: Settings = self.manager.settings_config.get_settings()

        self.twitch_worker: FetchFollowsWorker | None = None
        self.auth_worker: PlatformAuthWorker | None = None

        self.is_loading: bool = True

        self.init_ui()

    def _create_block(self, title: str, widget: QWidget) -> QWidget:
        """Helper to create a centered block with a title above the widget."""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 10)

        lbl = QLabel(title)
        lbl.setStyleSheet("font-weight: bold; color: #888;")

        layout.addWidget(lbl)
        layout.addWidget(widget)
        return container

    def init_ui(self) -> None:
        main_layout = QVBoxLayout(self)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_content = QWidget()

        content_layout = QVBoxLayout(scroll_content)
        content_layout.setAlignment(
            Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter
        )

        settings_container = QWidget()
        settings_container.setFixedWidth(450)
        form = QVBoxLayout(settings_container)
        form.setSpacing(5)

        quality_layout = QHBoxLayout()
        self.auto_quality_check: QCheckBox = QCheckBox("Enable")
        self.auto_quality_check.setChecked(self.settings.auto_select_quality[1])

        self.quality_combo: QComboBox = QComboBox()
        self.quality_combo.addItems([q.value for q in Quality])
        self.quality_combo.setCurrentText(self.settings.auto_select_quality[0].value)
        quality_layout.addWidget(self.auto_quality_check)
        quality_layout.addWidget(self.quality_combo)

        q_widget = QWidget()
        q_widget.setLayout(quality_layout)
        form.addWidget(self._create_block("Auto-Select Quality:", q_widget))

        self.pause_input: QKeySequenceEdit = QKeySequenceEdit(
            self.settings.default_pause_start_key
        )
        self.mute_input: QKeySequenceEdit = QKeySequenceEdit(
            self.settings.default_mute_unmute_key
        )
        form.addWidget(self._create_block("Default Pause/Start Key:", self.pause_input))
        form.addWidget(self._create_block("Default Mute/Unmute Key:", self.mute_input))

        self.chat_check: QCheckBox = QCheckBox("Enable Live Chat (Future)")
        self.chat_check.setChecked(self.settings.default_chat_active)
        form.addWidget(self._create_block("Default Chat Active:", self.chat_check))

        refresh_layout = QHBoxLayout()
        self.refresh_check: QCheckBox = QCheckBox("Enable")
        self.refresh_spin: QSpinBox = QSpinBox()
        self.refresh_spin.setRange(1, 1000)
        self.refresh_combo: QComboBox = QComboBox()
        self.refresh_combo.addItems(["Seconds", "Minutes", "Hours"])

        current_sec = int(self.settings.auto_refresh_sec)
        if current_sec == 0:
            self.refresh_check.setChecked(False)
            self.refresh_spin.setValue(60)
            self.refresh_combo.setCurrentText("Seconds")
        elif current_sec % 3600 == 0:
            self.refresh_check.setChecked(True)
            self.refresh_spin.setValue(current_sec // 3600)
            self.refresh_combo.setCurrentText("Hours")
        elif current_sec % 60 == 0:
            self.refresh_check.setChecked(True)
            self.refresh_spin.setValue(current_sec // 60)
            self.refresh_combo.setCurrentText("Minutes")
        else:
            self.refresh_check.setChecked(True)
            self.refresh_spin.setValue(current_sec)
            self.refresh_combo.setCurrentText("Seconds")

        refresh_layout.addWidget(self.refresh_check)
        refresh_layout.addWidget(self.refresh_spin)
        refresh_layout.addWidget(self.refresh_combo)

        r_widget = QWidget()
        r_widget.setLayout(refresh_layout)
        form.addWidget(self._create_block("Auto Refresh Stream List:", r_widget))

        self.theme_combo: QComboBox = QComboBox()
        self.theme_combo.addItems([t.value for t in Theme])
        self.theme_combo.setCurrentText(self.settings.dark_light_mode.value)
        form.addWidget(self._create_block("Theme:", self.theme_combo))

        vol_layout = QHBoxLayout()
        self.vol_slider: QSlider = QSlider(Qt.Orientation.Horizontal)
        self.vol_slider.setRange(0, 100)
        self.vol_slider.setValue(self.settings.default_volume_num)
        self.vol_label: QLabel = QLabel(f"{self.settings.default_volume_num}%")
        self.vol_label.setFixedWidth(40)

        vol_layout.addWidget(self.vol_slider)
        vol_layout.addWidget(self.vol_label)

        v_widget = QWidget()
        v_widget.setLayout(vol_layout)
        form.addWidget(self._create_block("Default Volume (0-100):", v_widget))

        form.addWidget(QLabel(""))

        self.btn_twitch: QPushButton = QPushButton("Import Twitch Follows")
        self.btn_edit_json: QPushButton = QPushButton("Edit streamify.json")
        self.btn_reset: QPushButton = QPushButton("RESET Stream List")
        self.btn_reset.setStyleSheet(
            "background-color: darkred; color: white; font-weight: bold;"
        )

        form.addWidget(self.btn_twitch)
        form.addWidget(self.btn_edit_json)
        form.addWidget(self.btn_reset)

        content_layout.addWidget(settings_container)
        scroll_area.setWidget(scroll_content)
        main_layout.addWidget(scroll_area)

        # ================== AUTO-SAVE CONNECTIONS ==================
        safe_connect(self.auto_quality_check.toggled, self.trigger_save)
        safe_connect(self.quality_combo.currentTextChanged, self.trigger_save)
        safe_connect(self.pause_input.keySequenceChanged, self.trigger_save)
        safe_connect(self.mute_input.keySequenceChanged, self.trigger_save)
        safe_connect(self.chat_check.toggled, self.trigger_save)
        safe_connect(self.refresh_check.toggled, self.trigger_save)
        safe_connect(self.refresh_spin.valueChanged, self.trigger_save)
        safe_connect(self.refresh_combo.currentTextChanged, self.trigger_save)
        safe_connect(self.theme_combo.currentTextChanged, self.trigger_save)

        safe_connect(self.vol_slider.valueChanged, self.set_vol_slider)
        safe_connect(self.vol_slider.valueChanged, self.trigger_save)

        safe_connect(self.btn_twitch.clicked, self.open_twitch_dialog)
        safe_connect(self.btn_edit_json.clicked, self.edit_json)
        safe_connect(self.btn_reset.clicked, self.reset_streams)

        self.is_loading = False

    # ==================== LOGIC ====================

    def set_vol_slider(self, value: int) -> None:
        self.vol_label.setText(f"{value}%")

    def trigger_save(self) -> None:
        """Dynamically saves settings whenever an input changes."""
        if self.is_loading:
            return

        self.settings.auto_select_quality = (
            Quality(self.quality_combo.currentText()),
            self.auto_quality_check.isChecked(),
        )
        self.settings.default_pause_start_key = (
            self.pause_input.keySequence().toString()
        )
        self.settings.default_mute_unmute_key = self.mute_input.keySequence().toString()
        self.settings.default_chat_active = self.chat_check.isChecked()
        self.settings.default_volume_num = self.vol_slider.value()

        if not self.refresh_check.isChecked():
            self.settings.auto_refresh_sec = 0.0
        else:
            val = self.refresh_spin.value()
            mult = self.refresh_combo.currentText()
            if mult == "Hours":
                self.settings.auto_refresh_sec = float(val * 3600)
            elif mult == "Minutes":
                self.settings.auto_refresh_sec = float(val * 60)
            else:
                self.settings.auto_refresh_sec = float(val)

        self.set_theme()
        self.manager.settings_config.set_settings(self.settings)

        self.manager.all_apply_settings()

        mw: Any = self.main_window
        if hasattr(mw, "home_tab"):
            mw.home_tab.apply_timer_settings()

    def set_theme(self) -> None:
        new_theme = Theme(self.theme_combo.currentText())
        if self.settings.dark_light_mode != new_theme:
            self.settings.dark_light_mode = new_theme

            app = QApplication.instance()
            if isinstance(app, QApplication):
                load_stylesheet(app, theme_name=new_theme.value)

    def open_twitch_dialog(self) -> None:
        """1-Click Twitch Login & Follow Import."""
        self.btn_twitch.setEnabled(False)
        self.btn_twitch.setText("Opening browser...")

        fetcher = FetcherFactory().get_fetcher("twitch", client_id=TWITCH_CLIENT_ID)

        self.auth_worker = PlatformAuthWorker(fetcher, port=TWITCH_REDIRECT_PORT)

        def on_auth_success(token: str) -> None:
            self.btn_twitch.setText("Fetching follows...")

            self.twitch_worker = FetchFollowsWorker(
                FetcherFactory().get_fetcher(
                    "twitch", client_id=TWITCH_CLIENT_ID, access_token=token
                )
            )

            def on_success(_streams: list[Stream]) -> None:
                existing_urls = {
                    s.url.lower() for _idx, s in self.manager.query_streams()
                }
                added_count = 0

                for s in _streams:
                    if s.url.lower() not in existing_urls:
                        _ = self.manager.add_stream(s.name, s.url, s.category_id)
                        existing_urls.add(s.url.lower())
                        added_count += 1

                mw: Any = self.main_window
                if hasattr(mw, "home_tab"):
                    mw.home_tab.refresh_stream_list()

                _ = QMessageBox.information(
                    self, "Success", f"Imported {added_count} new streams from Twitch!"
                )
                self.btn_twitch.setEnabled(True)
                self.btn_twitch.setText("Import Twitch Follows")

            def on_error(err: str) -> None:
                _ = QMessageBox.warning(
                    self, "Error", f"Failed fetching follows: {err}"
                )
                self.btn_twitch.setEnabled(True)
                self.btn_twitch.setText("Import Twitch Follows")

            safe_connect(self.twitch_worker.fetch_finished, on_success)
            safe_connect(self.twitch_worker.error, on_error)
            self.twitch_worker.start()

        def on_auth_error(err: str) -> None:
            _ = QMessageBox.warning(self, "Login Error", f"Twitch login failed: {err}")
            self.btn_twitch.setEnabled(True)
            self.btn_twitch.setText("Import Twitch Follows")

        safe_connect(self.auth_worker.auth_successful, on_auth_success)
        safe_connect(self.auth_worker.error, on_auth_error)
        self.auth_worker.start()

    def edit_json(self) -> None:
        reply = QMessageBox.question(
            self,
            "Edit Database",
            JSON_EDIT_WARNING,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                _ = QDesktopServices.openUrl(QUrl.fromLocalFile(STREAM_LIST))
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

            mw: Any = self.main_window
            if hasattr(mw, "home_tab"):
                mw.home_tab.refresh_stream_list()

            _ = QMessageBox.information(
                self,
                "Reset Complete",
                JSON_EDIT_NOTE,
            )
