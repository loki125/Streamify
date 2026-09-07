from __future__ import annotations

from typing import Any

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtCore.QtWidgets import (
    QGridLayout,
    QHBoxLayout,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from streamify.backend.core.models import Settings, Stream
from streamify.backend.fetcher_factory import FetcherFactory

# --- BACKEND IMPORTS ---
from streamify.backend.manager import StreamlinkManager
from streamify.backend.settings import SettingsConfig

from .utils import dialogs
from .utils.signals import FetchFollowsWorker, QualityCheckWorker

# --- UI IMPORTS ---
from .utils.widgets import StreamListItemWidget, VideoPlayerFrame


class MainWindow(QMainWindow):
    stream_error_signal: Any = pyqtSignal(str)

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Streamify")
        self.resize(1200, 720)

        # 1. Initialize Backend
        self.settings_config: SettingsConfig = SettingsConfig()
        self.settings: Settings = self.settings_config.get_settings()
        self.manager: StreamlinkManager = StreamlinkManager()

        self.stream_error_signal.connect(self.show_stream_error)

        self.init_ui()

        self.refresh_stream_list()

    def init_ui(self) -> None:
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)

        # ==================== SIDEBAR ====================
        sidebar_widget = QWidget()
        sidebar_layout = QVBoxLayout(sidebar_widget)

        top_left_layout = QHBoxLayout()
        self.btn_settings: Any = QPushButton("Settings")
        self.btn_fetch_twitch: Any = QPushButton("Fetch Twitch Follows")
        top_left_layout.addWidget(self.btn_settings)
        top_left_layout.addWidget(self.btn_fetch_twitch)
        sidebar_layout.addLayout(top_left_layout)

        controls_layout = QHBoxLayout()
        self.btn_add_stream: Any = QPushButton("Add Stream")
        self.btn_check_status: Any = QPushButton("Check Statuses")
        controls_layout.addWidget(self.btn_add_stream)
        controls_layout.addWidget(self.btn_check_status)
        sidebar_layout.addLayout(controls_layout)

        self.stream_list_widget: Any = QListWidget()
        sidebar_layout.addWidget(self.stream_list_widget)

        splitter.addWidget(sidebar_widget)

        video_area_widget = QWidget()
        self.video_grid: Any = QGridLayout(video_area_widget)

        self.video_frames: list[VideoPlayerFrame] = []
        for i in range(4):
            frame = VideoPlayerFrame(player_id=i + 1)
            self.video_frames.append(frame)
            row, col = divmod(i, 2)
            self.video_grid.addWidget(frame, row, col)

        for frame in self.video_frames:
            click_sig: Any = frame.clicked
            click_sig.connect(self.stop_stream_in_frame)

        splitter.addWidget(video_area_widget)
        splitter.setSizes([300, 900])

        # Bind signals
        self.btn_settings.clicked.connect(self.open_settings)
        self.btn_fetch_twitch.clicked.connect(self.fetch_twitch_follows)
        self.btn_add_stream.clicked.connect(self.add_stream_manually)
        self.btn_check_status.clicked.connect(self.check_statuses)

    # ==================== LOGIC ====================
    def refresh_stream_list(self) -> None:
        self.stream_list_widget.clear()
        streams = self.manager.query_streams()

        # USE enumerate() TO GET THE INDEX (stream_id)
        for index, stream in enumerate(streams):
            item = QListWidgetItem(self.stream_list_widget)
            widget = StreamListItemWidget(stream, stream_id=index)

            widget.launch_requested.connect(self.launch_stream_prompt)
            widget.remove_requested.connect(self.remove_stream)

            item.setSizeHint(widget.sizeHint())
            self.stream_list_widget.addItem(item)
            self.stream_list_widget.setItemWidget(item, widget)

    def launch_stream_prompt(self, stream_id: int, stream: Any) -> None:
        """Step 1: User clicks launch. Start fetching qualities."""
        available_frame = next(
            (f for f in self.video_frames if f.active_stream_id is None), None
        )
        if not available_frame:
            QMessageBox.warning(
                self, "Error", "No available video players. Stop a stream first."
            )
            return

        QMessageBox.information(
            self,
            "Fetching",
            "Fetching available stream qualities...\nPlease wait a moment.",
            QMessageBox.StandardButton.Ok,
        )

        # Pass stream_id (index) to the worker
        self.quality_worker: QualityCheckWorker = QualityCheckWorker(
            self.manager, stream_id, stream
        )
        self.quality_worker.finished.connect(self.on_qualities_fetched)
        self.quality_worker.start()

    def on_qualities_fetched(
        self, available_qualities: list[str], stream_id: int, stream: Any
    ) -> None:
        """Step 2: Qualities fetched. Ask user and launch."""
        if not available_qualities:
            reply = QMessageBox.warning(
                self,
                "Warning",
                "Could not fetch qualities. Stream might be offline. Try launching anyway with 'best'?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply == QMessageBox.StandardButton.No:
                return

        selected_quality = dialogs.ask_quality_dialog(self, available_qualities)
        if not selected_quality:
            return

        available_frame = next(
            (f for f in self.video_frames if f.active_stream_id is None), None
        )
        if not available_frame:
            return

        win_id = available_frame.get_win_id()
        stream_name = getattr(stream, "name", f"Stream {stream_id}")

        available_frame.set_active(stream_name, stream_id)

        def on_error_callback(failed_stream_id: int, error_msg: str) -> None:

            error_signal: Any = self.stream_error_signal
            error_signal.emit(f"Error playing {stream_name}: {error_msg}")

            if available_frame.active_stream_id == failed_stream_id:
                available_frame.set_idle()

        self.manager.launch_stream(
            stream_id, win_id, selected_quality, on_error_callback
        )

    def remove_stream(self, stream_id: int, stream: Any) -> None:
        stream_name = getattr(stream, "name", "this stream")
        if dialogs.confirm_remove_stream(self, stream_name):
            # Pass the index to manager
            self.manager.remove_stream(stream_id)
            self.refresh_stream_list()

    def on_statuses_checked(self, statuses: dict[int, bool]) -> None:
        self.btn_check_status.setEnabled(True)
        self.btn_check_status.setText("Check Statuses")

        for i in range(self.stream_list_widget.count()):
            item = self.stream_list_widget.item(i)
            widget: StreamListItemWidget = self.stream_list_widget.itemWidget(item)

            # Since widget.stream_id is explicitly set to the index,
            # we can use it to check the statuses dictionary directly!
            if widget.stream_id in statuses:
                _ = widget.update_status(statuses[widget.stream_id])

    def fetch_twitch_follows(self) -> None:
        self.btn_fetch_twitch.setEnabled(False)
        self.btn_fetch_twitch.setText("Fetching...")

        self.fetch_worker: FetchFollowsWorker = FetchFollowsWorker(
            FetcherFactory, "twitch"
        )
        self.fetch_worker.finished.connect(self.on_fetch_success)
        self.fetch_worker.error.connect(self.on_fetch_error)
        self.fetch_worker.start()

    def on_fetch_success(self, streams: list[Stream]) -> None:
        self.btn_fetch_twitch.setEnabled(True)
        self.btn_fetch_twitch.setText("Fetch Twitch Follows")
        for stream in streams:
            self.manager.add_stream(stream)
        self.refresh_stream_list()
        QMessageBox.information(self, "Success", f"Imported {len(streams)} streams.")

    def on_fetch_error(self, error_msg: str) -> None:
        self.btn_fetch_twitch.setEnabled(True)
        self.btn_fetch_twitch.setText("Fetch Twitch Follows")
        QMessageBox.critical(
            self, "Fetch Error", f"Failed to fetch streams: {error_msg}"
        )

    def open_settings(self) -> None:
        QMessageBox.information(self, "Settings", "Settings Menu coming soon.")

    def add_stream_manually(self) -> None:
        name = dialogs.ask_stream_name_dialog(self)
        if name:
            QMessageBox.information(
                self,
                "Note",
                "Update 'add_stream_manually' with your backend Stream creation logic.",
            )
            self.refresh_stream_list()

    def show_stream_error(self, message: str) -> None:
        QMessageBox.warning(self, "Playback Error", message)

    def closeEvent(self, event: Any) -> None:
        for frame in self.video_frames:
            if frame.active_stream_id is not None:
                self.manager.stop_stream(frame.active_stream_id)
        super().closeEvent(event)
