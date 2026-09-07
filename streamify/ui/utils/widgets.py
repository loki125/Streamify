from __future__ import annotations

from typing import Any

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtCore.QtGui import QMouseEvent
from PyQt6.QtCore.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class VideoPlayerFrame(QFrame):
    """A designated window for MPV to attach to using its Window ID (wid)."""

    clicked: Any = pyqtSignal()

    def __init__(self, player_id: int) -> None:
        super().__init__()
        self.player_id: int = player_id
        self.active_stream_id: int | None = None
        self.setStyleSheet("background-color: black; border: 1px solid #333;")

        self.layout = QVBoxLayout(self)
        self.label = QLabel(f"Player {self.player_id}\nIdle")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setStyleSheet("color: white;")
        self.layout.addWidget(self.label)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        click_sig: Any = self.clicked
        click_sig.emit(
            self
        )  # Emit 'self' so the main window knows WHICH frame was clicked
        super().mousePressEvent(event)

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

    # Signals now emit (index, stream_object)
    launch_requested = pyqtSignal(int, object)
    remove_requested = pyqtSignal(int, object)

    def __init__(self, stream: Any, stream_id: int) -> None:
        super().__init__()
        self.stream = stream
        self.stream_id = stream_id  # Save the list index!

        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        self.status_lbl = QLabel("⚫")
        self.name_lbl = QLabel(getattr(stream, "name", "Unknown Stream"))

        self.launch_btn = QPushButton("Launch")
        self.remove_btn = QPushButton("X")
        self.remove_btn.setFixedWidth(30)

        layout.addWidget(self.status_lbl)
        layout.addWidget(self.name_lbl, stretch=1)
        layout.addWidget(self.launch_btn)
        layout.addWidget(self.remove_btn)

        # Emit both the index (stream_id) and the stream object
        self.launch_btn.clicked.connect(
            lambda: self.launch_requested.emit(self.stream_id, self.stream)
        )
        self.remove_btn.clicked.connect(
            lambda: self.remove_requested.emit(self.stream_id, self.stream)
        )

    def update_status(self, is_live: bool) -> None:
        if is_live:
            self.status_lbl.setText("🟢")
            self.status_lbl.setToolTip("Live")
        else:
            self.status_lbl.setText("🔴")
            self.status_lbl.setToolTip("Offline")
