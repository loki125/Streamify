# pyright: reportUnknownMemberType=none
from __future__ import annotations

from typing import override

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
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

# ADDED: StatusCheckerWorker to imports
from .utils.signals import FetchFollowsWorker, QualityCheckWorker, StatusCheckerWorker

# --- UI IMPORTS ---
from .utils.widgets import StreamListItemWidget, VideoPlayerFrame


class MainWindow(QMainWindow):
    stream_error_signal: pyqtSignal = pyqtSignal(str)

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Streamify")
        self.resize(1200, 720)

        # FIXED: Declare and initialize workers to None to satisfy strict typing
        self.fetch_worker: FetchFollowsWorker | None = None
        self.quality_worker: QualityCheckWorker | None = None
        self.status_worker: StatusCheckerWorker | None = None

        self.settings_config: SettingsConfig = SettingsConfig()
        self.settings: Settings = self.settings_config.get_settings()
        self.manager: StreamlinkManager = StreamlinkManager()

        _ = self.stream_error_signal.connect(self.show_stream_error)

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
        self.btn_settings: QPushButton = QPushButton("Settings")
        self.btn_fetch_twitch: QPushButton = QPushButton("Fetch Twitch Follows")
        top_left_layout.addWidget(self.btn_settings)
        top_left_layout.addWidget(self.btn_fetch_twitch)
        sidebar_layout.addLayout(top_left_layout)

        controls_layout = QHBoxLayout()
        self.btn_add_stream: QPushButton = QPushButton("Add Stream")
        self.btn_check_status: QPushButton = QPushButton("Check Statuses")
        controls_layout.addWidget(self.btn_add_stream)
        controls_layout.addWidget(self.btn_check_status)
        sidebar_layout.addLayout(controls_layout)

        self.stream_list_widget: QListWidget = QListWidget()
        sidebar_layout.addWidget(self.stream_list_widget)

        splitter.addWidget(sidebar_widget)

        video_area_widget = QWidget()
        self.video_grid: QGridLayout = QGridLayout(video_area_widget)

        self.video_frames: list[VideoPlayerFrame] = []
        for i in range(4):
            frame = VideoPlayerFrame(player_id=i + 1)
            self.video_frames.append(frame)
            row, col = divmod(i, 2)
            self.video_grid.addWidget(frame, row, col)

        for frame in self.video_frames:
            click_sig = frame.clicked
            _ = click_sig.connect(self.stop_stream_in_frame)

        splitter.addWidget(video_area_widget)
        splitter.setSizes([300, 900])

        # Bind signals
        _ = self.btn_settings.clicked.connect(self.open_settings)
        _ = self.btn_fetch_twitch.clicked.connect(self.fetch_twitch_follows)
        _ = self.btn_add_stream.clicked.connect(self.add_stream_manually)
        _ = self.btn_check_status.clicked.connect(self.check_statuses)

    def stop_stream_in_frame(self, frame: VideoPlayerFrame) -> None:
        """Stops the stream running in a specific frame when clicked."""
        if frame.active_stream_id is not None and dialogs.confirm_stop_stream(self):
            self.manager.stop_stream(frame.active_stream_id)
            frame.set_idle()

    # ==================== LOGIC ====================
    def refresh_stream_list(self) -> None:
        self.stream_list_widget.clear()
        streams = self.manager.query_streams()

        # USE enumerate() TO GET THE INDEX (stream_id)
        for index, stream in enumerate(streams):
            item = QListWidgetItem(self.stream_list_widget)
            widget = StreamListItemWidget(stream, stream_id=index)

            _ = widget.launch_requested.connect(self.launch_stream_prompt)
            _ = widget.remove_requested.connect(self.remove_stream)

            item.setSizeHint(widget.sizeHint())
            self.stream_list_widget.addItem(item)
            self.stream_list_widget.setItemWidget(item, widget)

    def launch_stream_prompt(self, stream_id: int, stream: Stream) -> None:
        """Step 1: User clicks launch. Start fetching qualities."""
        available_frame = next(
            (f for f in self.video_frames if f.active_stream_id is None), None
        )
        if not available_frame:
            _ = QMessageBox.warning(
                self, "Error", "No available video players. Stop a stream first."
            )
            return

        _ = QMessageBox.information(
            self,
            "Fetching",
            "Fetching available stream qualities...\nPlease wait a moment.",
            QMessageBox.StandardButton.Ok,
        )

        # FIXED: Removed the inline type hint since it's already in __init__
        self.quality_worker = QualityCheckWorker(self.manager, stream_id, stream)
        _ = self.quality_worker.finished.connect(self.on_qualities_fetched)
        self.quality_worker.start()

    def on_qualities_fetched(
        self, available_qualities: list[str], stream_id: int, stream: Stream
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

        available_frame.set_active(stream.name, stream_id)

        def on_error_callback(failed_stream_id: int, error_msg: str) -> None:
            error_signal = self.stream_error_signal
            error_signal.emit(f"Error playing {stream.name}: {error_msg}")

            if available_frame.active_stream_id == failed_stream_id:
                available_frame.set_idle()

        self.manager.launch_stream(
            stream_id, win_id, selected_quality, on_error_callback
        )

    def remove_stream(self, stream_id: int, stream: Stream) -> None:
        if dialogs.confirm_remove_stream(self, stream.name):
            self.manager.remove_stream(stream_id)
            self.refresh_stream_list()

    # ADDED: The missing check_statuses method!
    def check_statuses(self) -> None:
        self.btn_check_status.setEnabled(False)
        self.btn_check_status.setText("Checking...")

        self.status_worker = StatusCheckerWorker(self.manager)
        _ = self.status_worker.finished.connect(self.on_statuses_checked)
        self.status_worker.start()

    def on_statuses_checked(self, statuses: dict[int, bool]) -> None:
        self.btn_check_status.setEnabled(True)
        self.btn_check_status.setText("Check Statuses")

        for i in range(self.stream_list_widget.count()):
            item = self.stream_list_widget.item(i)
            if item is None:
                continue

            widget = self.stream_list_widget.itemWidget(item)

            if (
                isinstance(widget, StreamListItemWidget)
                and widget.stream_id in statuses
            ):
                widget.update_status(statuses[widget.stream_id])

    def fetch_twitch_follows(self) -> None:
        self.btn_fetch_twitch.setEnabled(False)
        self.btn_fetch_twitch.setText("Fetching...")

        # FIXED: Removed the inline type hint
        self.fetch_worker = FetchFollowsWorker(FetcherFactory, "twitch")
        _ = self.fetch_worker.finished.connect(self.on_fetch_success)
        _ = self.fetch_worker.error.connect(self.on_fetch_error)
        self.fetch_worker.start()

    def on_fetch_success(self, streams: list[Stream]) -> None:
        self.btn_fetch_twitch.setEnabled(True)
        self.btn_fetch_twitch.setText("Fetch Twitch Follows")
        for stream in streams:
            self.manager.add_stream(stream)
        self.refresh_stream_list()
        _ = QMessageBox.information(
            self, "Success", f"Imported {len(streams)} streams."
        )

    def on_fetch_error(self, error_msg: str) -> None:
        self.btn_fetch_twitch.setEnabled(True)
        self.btn_fetch_twitch.setText("Fetch Twitch Follows")
        _ = QMessageBox.critical(
            self, "Fetch Error", f"Failed to fetch streams: {error_msg}"
        )

    def open_settings(self) -> None:
        _ = QMessageBox.information(self, "Settings", "Settings Menu coming soon.")

    def add_stream_manually(self) -> None:
        name = dialogs.ask_stream_name_dialog(self)
        if name:
            _ = QMessageBox.information(
                self,
                "Note",
                "Update 'add_stream_manually' with your backend Stream creation logic.",
            )
            self.refresh_stream_list()

    def show_stream_error(self, message: str) -> None:
        _ = QMessageBox.warning(self, "Playback Error", message)

    @override
    def closeEvent(self, a0) -> None:
        for frame in self.video_frames:
            if frame.active_stream_id is not None:
                self.manager.stop_stream(frame.active_stream_id)
        super().closeEvent(a0)
