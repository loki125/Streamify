# pyright: reportUnknownMemberType=none
from __future__ import annotations

from typing import Any, override

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QCloseEvent, QContextMenuEvent
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMdiSubWindow,
    QMenu,
    QPushButton,
    QWidget,
)

from streamify.backend.core.models import Stream
from streamify.backend.manager import StreamlinkManager


class StreamVideoWindow(QMdiSubWindow):
    """A floating/tabbed sub-window that houses the MPV player."""

    def __init__(
        self, stream_id: int, stream_name: str, manager: StreamlinkManager
    ) -> None:
        super().__init__()
        self.stream_id: int = stream_id
        self.manager: StreamlinkManager = manager

        self.setWindowTitle(stream_name)
        self.setMinimumSize(640, 360)

        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)

        self.video_frame: QFrame = QFrame()
        self.video_frame.setStyleSheet("background-color: black;")
        self.video_frame.setAttribute(Qt.WidgetAttribute.WA_NativeWindow, True)

        self.setWidget(self.video_frame)

    def get_win_id(self) -> int:
        return int(self.video_frame.winId())

    @override
    def closeEvent(self, closeEvent: QCloseEvent | None) -> None:
        """When the user clicks the 'X', tell the backend to stop the stream."""
        self.manager.stop_stream(self.stream_id)
        super().closeEvent(closeEvent)


class StreamListItemWidget(QWidget):
    launch_requested: pyqtSignal = pyqtSignal(int, object)
    custom_settings_requested: pyqtSignal = pyqtSignal(int, object)
    edit_requested: pyqtSignal = pyqtSignal(int, object)
    status_check_requested: pyqtSignal = pyqtSignal(int, object)
    remove_requested: pyqtSignal = pyqtSignal(int, object)

    def __init__(self, stream: Stream, stream_id: int) -> None:
        super().__init__()
        self.stream: Stream = stream
        self.stream_id: int = stream_id

        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        self.status_lbl: QLabel = QLabel("-")
        self.name_lbl: QLabel = QLabel(self.stream.name)

        self.launch_btn: QPushButton = QPushButton("▶︎ Launch")

        layout.addWidget(self.status_lbl)
        layout.addWidget(self.name_lbl, stretch=1)
        layout.addWidget(self.launch_btn)

        sig: Any = self.launch_btn.clicked
        sig.connect(lambda: self.launch_requested.emit(self.stream_id, self.stream))

    @override
    def contextMenuEvent(self, a0: QContextMenuEvent | None) -> None:
        if not a0:
            return

        menu = QMenu(self)

        edit_action = menu.addAction("✍︎ Edit")
        check_action = menu.addAction("⚫ Check Status")
        settings_action = menu.addAction("⚙️ Custom Settings")
        _ = menu.addSeparator()
        remove_action = menu.addAction("✖ Remove")

        action = menu.exec(a0.globalPos())

        if action == edit_action:
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
            self.status_lbl.setStyleSheet("color: green")
            self.status_lbl.setToolTip("Live")
        else:
            self.status_lbl.setText("⊝")
            self.status_lbl.setStyleSheet("color: grey")
            self.status_lbl.setToolTip("Offline")
