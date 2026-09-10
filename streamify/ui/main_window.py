# pyright: reportUnknownMemberType=none
from __future__ import annotations

from typing import override

from PyQt6.QtGui import QCloseEvent
from PyQt6.QtWidgets import QMainWindow, QTabWidget, QVBoxLayout, QWidget

from streamify.backend.manager import StreamlinkManager
from streamify.backend.settings import SettingsConfig

from .tabs.home_tab import HomeTab
from .tabs.settings_tab import SettingsTab
from .tabs.twitch_tab import TwitchTab


class MainWindow(QMainWindow):
    def __init__(self, manager: StreamlinkManager) -> None:
        super().__init__()
        self.setWindowTitle("Streamify")
        self.resize(1200, 720)

        self.settings_config: SettingsConfig = SettingsConfig()
        self.manager: StreamlinkManager = manager

        self.init_ui()

    def init_ui(self) -> None:
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)

        self.tabs: QTabWidget = QTabWidget()
        main_layout.addWidget(self.tabs)

        self.home_tab: HomeTab = HomeTab(self.manager, self.settings_config)
        self.settings_tab: SettingsTab = SettingsTab()
        self.twitch_tab: TwitchTab = TwitchTab()

        _ = self.tabs.addTab(self.home_tab, "☰ Home")
        _ = self.tabs.addTab(self.settings_tab, "⚙️ Settings")
        _ = self.tabs.addTab(self.twitch_tab, "☕︎ Twitch")

    @override
    def closeEvent(self, a0: QCloseEvent | None) -> None:
        """Ensure all streams close when the app is exited."""
        self.home_tab.close_all_streams()
        super().closeEvent(a0)
