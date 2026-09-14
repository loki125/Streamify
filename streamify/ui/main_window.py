# pyright: reportUnknownMemberType=none
from __future__ import annotations

from typing import override

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QCloseEvent, QKeySequence, QShortcut
from PyQt6.QtWidgets import (
    QKeySequenceEdit,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QTabBar,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from streamify.backend.manager import StreamlinkManager

from .tabs.home_tab import HomeTab
from .tabs.settings_tab import SettingsTab
from .utils.signals import safe_connect


class MainWindow(QMainWindow):
    def __init__(self, manager: StreamlinkManager) -> None:
        super().__init__()
        self.setWindowTitle("Streamify")
        self.resize(1200, 720)

        self.manager: StreamlinkManager = manager
        self.init_ui()

    def init_ui(self) -> None:
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)

        self.tabs: QTabWidget = QTabWidget()
        main_layout.addWidget(self.tabs)

        self.btn_fullscreen: QPushButton = QPushButton("⌞ ⌝")
        self.btn_fullscreen.setToolTip("Toggle Fullscreen (F)")
        self.btn_fullscreen.setCursor(Qt.CursorShape.PointingHandCursor)
        safe_connect(self.btn_fullscreen.clicked, self.toggle_fullscreen)

        self.tabs.setCornerWidget(self.btn_fullscreen, Qt.Corner.TopRightCorner)

        self.home_tab: HomeTab = HomeTab(self.manager)
        self.settings_tab: SettingsTab = SettingsTab(self.manager, self)

        _ = self.tabs.addTab(self.home_tab, "☰ Home")
        _ = self.tabs.addTab(self.settings_tab, "⚙️ Settings")

        self.shortcut_f: QShortcut = QShortcut(QKeySequence("F"), self)
        _ = self.shortcut_f.activated.connect(self.toggle_fullscreen)

        self.shortcut_f11: QShortcut = QShortcut(QKeySequence("F11"), self)
        _ = self.shortcut_f11.activated.connect(self.toggle_fullscreen)

        self.shortcut_esc: QShortcut = QShortcut(QKeySequence("Escape"), self)
        _ = self.shortcut_esc.activated.connect(self.exit_fullscreen)

    @override
    def closeEvent(self, a0: QCloseEvent | None) -> None:
        """Ensure all streams close when the app is exited."""
        self.home_tab.close_all_streams()
        super().closeEvent(a0)

    def toggle_fullscreen(self) -> None:
        """Toggles true fullscreen for the active stream without breaking MPV."""
        focused = self.focusWidget()
        if isinstance(focused, (QLineEdit, QKeySequenceEdit)):
            return

        if not self.home_tab.mdi_area.subWindowList():
            return

        if self.isFullScreen():
            self.exit_fullscreen()
        else:
            self.enter_fullscreen()

    def enter_fullscreen(self) -> None:
        """Hides all UI bars and maximizes the video across the whole monitor."""
        tabbar = self.tabs.tabBar()
        if tabbar is not None:
            tabbar.hide()
        self.home_tab.sidebar_widget.hide()

        mdi_tab_bar = self.home_tab.mdi_area.findChild(QTabBar)
        if mdi_tab_bar:
            mdi_tab_bar.hide()

        self.showFullScreen()

    def exit_fullscreen(self) -> None:
        """Restores the normal UI layout."""
        if not self.isFullScreen():
            return

        tabbar = self.tabs.tabBar()
        if tabbar is not None:
            tabbar.show()
        self.home_tab.sidebar_widget.show()

        mdi_tab_bar = self.home_tab.mdi_area.findChild(QTabBar)
        if mdi_tab_bar:
            mdi_tab_bar.show()

        self.showNormal()
