# pyright: reportUnknownMemberType=none
from __future__ import annotations

from typing import Any, override

from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import (
    QCloseEvent,
    QContextMenuEvent,
    QKeySequence,
    QMouseEvent,
    QShortcut,
)
from PyQt6.QtWidgets import (
    QDockWidget,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMenu,
    QWidget,
)

from streamify.backend.core.models import Stream
from streamify.backend.manager import StreamlinkManager


class StreamVideoWindow(QDockWidget):
    """A dockable window that houses the MPV player. Can be split, tabbed, or snapped."""

    def __init__(
        self,
        stream_id: int,
        stream_name: str,
        manager: StreamlinkManager,
        pause_key: str = "",
        mute_key: str = "",
    ) -> None:
        super().__init__(stream_name)

        self.stream_id: int = stream_id
        self.manager: StreamlinkManager = manager

        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)

        self.setFeatures(
            QDockWidget.DockWidgetFeature.DockWidgetClosable
            | QDockWidget.DockWidgetFeature.DockWidgetMovable
            | QDockWidget.DockWidgetFeature.DockWidgetFloatable
        )

        self.setContentsMargins(0, 0, 0, 0)

        self.video_frame: QFrame = QFrame(self)
        self.video_frame.setStyleSheet("background-color: black;")
        self.video_frame.setAttribute(Qt.WidgetAttribute.WA_NativeWindow, True)
        self.video_frame.setContentsMargins(0, 0, 0, 0)

        self.setWidget(self.video_frame)

        if pause_key:
            self.pause_shortcut: QShortcut = QShortcut(QKeySequence(pause_key), self)
            _ = self.pause_shortcut.activated.connect(
                lambda: self.manager.toggle_pause(self.stream_id)
            )

        if mute_key:
            self.mute_shortcut: QShortcut = QShortcut(QKeySequence(mute_key), self)
            _ = self.mute_shortcut.activated.connect(
                lambda: self.manager.toggle_mute(self.stream_id)
            )

    def get_win_id(self) -> int:
        return int(self.video_frame.winId())

    @override
    def closeEvent(self, event: QCloseEvent | None) -> None:
        """When the user clicks the 'X', tell the backend to stop the stream."""
        self.manager.stop_stream(self.stream_id)
        super().closeEvent(event)


class StreamListItemWidget(QWidget):
    launch_override_requested: pyqtSignal = pyqtSignal(int, object)
    launch_new_requested: pyqtSignal = pyqtSignal(int, object)

    custom_settings_requested: pyqtSignal = pyqtSignal(int, object)
    edit_requested: pyqtSignal = pyqtSignal(int, object)
    status_check_requested: pyqtSignal = pyqtSignal(int, object)
    remove_requested: pyqtSignal = pyqtSignal(int, object)

    def __init__(self, stream: Stream, stream_id: int) -> None:
        super().__init__()
        self.stream: Stream = stream
        self.stream_id: int = stream_id

        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 0, 6, 0)
        layout.setSpacing(8)
        layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        self.status_lbl: QLabel = QLabel("-")
        self.name_lbl: QLabel = QLabel(self.stream.name)

        layout.addWidget(self.status_lbl)
        layout.addWidget(self.name_lbl, stretch=1)

        self._click_timer: QTimer = QTimer(self)
        self._click_timer.setSingleShot(True)

        _ = self._click_timer.timeout.connect(self._on_single_click)

    @override
    def mousePressEvent(self, a0: QMouseEvent | None) -> None:
        if a0 and a0.button() == Qt.MouseButton.LeftButton:
            self._click_timer.start(250)
        super().mousePressEvent(a0)

    @override
    def mouseDoubleClickEvent(self, a0: QMouseEvent | None) -> None:
        if a0 and a0.button() == Qt.MouseButton.LeftButton:
            self._click_timer.stop()
            sig: Any = self.launch_new_requested
            sig.emit(self.stream_id, self.stream)
        super().mouseDoubleClickEvent(a0)

    def _on_single_click(self) -> None:
        """Triggered if 250ms passes without a second click."""
        sig: Any = self.launch_override_requested
        sig.emit(self.stream_id, self.stream)

    @override
    def contextMenuEvent(self, a0: QContextMenuEvent | None) -> None:
        if not a0:
            return

        menu = QMenu(self)

        launch_new_action = menu.addAction("➜] Launch in New Window")
        _ = menu.addSeparator()
        edit_action = menu.addAction("✍︎ Edit")
        check_action = menu.addAction("⚫ Check Status")
        settings_action = menu.addAction("⚙️ Custom Settings")
        _ = menu.addSeparator()
        remove_action = menu.addAction("✖ Remove")

        action = menu.exec(a0.globalPos())

        if action == launch_new_action:
            sig0: Any = self.launch_new_requested
            sig0.emit(self.stream_id, self.stream)
        elif action == edit_action:
            sig: Any = self.edit_requested
            sig.emit(self.stream_id, self.stream)
        elif action == check_action:
            sig2: Any = self.status_check_requested
            sig2.emit(self.stream_id, self.stream)
        elif action == remove_action:
            sig3: Any = self.remove_requested
            sig3.emit(self.stream_id, self.stream)
        elif action == settings_action:
            sig4: Any = self.custom_settings_requested
            sig4.emit(self.stream_id, self.stream)

    def update_status(self, is_live: bool) -> None:
        if is_live:
            self.status_lbl.setText("◉")
            self.status_lbl.setStyleSheet("color: green; font-size: 20px;")
            self.status_lbl.setToolTip("Live")
        else:
            self.status_lbl.setText("⊝")
            self.status_lbl.setStyleSheet("color: grey; font-size: 20px;")
            self.status_lbl.setToolTip("Offline")
