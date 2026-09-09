# pyright: reportUnknownMemberType=none
from __future__ import annotations

from typing import Any, override

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QCloseEvent
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMdiSubWindow,
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

        self.video_frame: QFrame = QFrame()
        self.video_frame.setStyleSheet("background-color: black;")
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

    def __init__(self, stream: Stream, stream_id: int) -> None:
        super().__init__()
        self.stream: Stream = stream
        self.stream_id: int = stream_id

        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        self.status_lbl: QLabel = QLabel("⚫")
        self.name_lbl: QLabel = QLabel(self.stream.name)

        self.launch_btn: QPushButton = QPushButton("Launch")

        layout.addWidget(self.status_lbl)
        layout.addWidget(self.name_lbl, stretch=1)
        layout.addWidget(self.launch_btn)

        sig: Any = self.launch_btn.clicked
        sig.connect(lambda: self.launch_requested.emit(self.stream_id, self.stream))

    def update_status(self, is_live: bool) -> None:
        if is_live:
            self.status_lbl.setText("🟢")
            self.status_lbl.setToolTip("Live")
        else:
            self.status_lbl.setText("🔴")
            self.status_lbl.setToolTip("Offline")
