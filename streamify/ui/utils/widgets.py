# pyright: reportUnknownMemberType=none
from __future__ import annotations

from typing import override

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QMouseEvent
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from streamify.backend.core.models import Stream


class VideoPlayerFrame(QFrame):
    """A designated window for MPV to attach to using its Window ID (wid)."""

    clicked: pyqtSignal = pyqtSignal()

    def __init__(self, player_id: int) -> None:
        super().__init__()
        self.player_id: int = player_id
        self.active_stream_id: int | None = None
        self.setStyleSheet("background-color: black; border: 1px solid #333;")

        layout = QVBoxLayout(self)
        self.label: QLabel = QLabel(f"Player {self.player_id}\nIdle")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setStyleSheet("color: white;")
        layout.addWidget(self.label)

    @override
    def mousePressEvent(self, a0: QMouseEvent | None) -> None:
        self.clicked.emit(self)
        super().mousePressEvent(a0)

    def get_win_id(self) -> int:
        return int(self.winId())

    def set_active(self, stream_name: str, stream_id: int) -> None:
        self.active_stream_id = stream_id
        self.label.setText(f"Playing: {stream_name}\n(Stream ID: {stream_id})")

    def set_idle(self) -> None:
        self.active_stream_id = None
        self.label.setText(f"Player {self.player_id}\nIdle")


class StreamListItemWidget(QWidget):
    """Custom widget for each row in the stream list sidebar."""

    launch_requested: pyqtSignal = pyqtSignal(int, object)
    remove_requested: pyqtSignal = pyqtSignal(int, object)

    def __init__(self, stream: Stream, stream_id: int) -> None:
        super().__init__()
        self.stream: Stream = stream
        self.stream_id: int = stream_id

        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        self.status_lbl: QLabel = QLabel("⚫")
        self.name_lbl: QLabel = QLabel(getattr(stream, "name", "Unknown Stream"))

        self.launch_btn: QPushButton = QPushButton("Launch")
        self.remove_btn: QPushButton = QPushButton("X")
        self.remove_btn.setFixedWidth(30)

        layout.addWidget(self.status_lbl)
        layout.addWidget(self.name_lbl, stretch=1)
        layout.addWidget(self.launch_btn)
        layout.addWidget(self.remove_btn)

        # Emit both the index (stream_id) and the stream object
        _ = self.launch_btn.clicked.connect(
            lambda: self.launch_requested.emit(self.stream_id, self.stream)
        )
        _ = self.remove_btn.clicked.connect(
            lambda: self.remove_requested.emit(self.stream_id, self.stream)
        )

    def update_status(self, is_live: bool) -> None:
        if is_live:
            self.status_lbl.setText("🟢")
            self.status_lbl.setToolTip("Live")
        else:
            self.status_lbl.setText("🔴")
            self.status_lbl.setToolTip("Offline")
