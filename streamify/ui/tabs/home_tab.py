# pyright: reportUnknownMemberType=none
from __future__ import annotations

from typing import Any

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMdiArea,
    QMessageBox,
    QPushButton,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from streamify.backend.core.models import Stream
from streamify.backend.manager import StreamlinkManager
from streamify.backend.settings import SettingsConfig

from ..utils import dialogs
from ..utils.signals import LaunchPrecheckWorker, safe_connect
from ..utils.widgets import StreamListItemWidget, StreamVideoWindow


class HomeTab(QWidget):
    stream_error_signal: pyqtSignal = pyqtSignal(str)

    def __init__(
        self, manager: StreamlinkManager, settings_config: SettingsConfig
    ) -> None:
        super().__init__()
        self.manager: StreamlinkManager = manager
        self.settings_config: SettingsConfig = settings_config

        self.active_workers: list[LaunchPrecheckWorker] = []

        safe_connect(self.stream_error_signal, self.show_stream_error)
        self.init_ui()
        self.refresh_stream_list()

    def init_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(splitter)

        # ==================== LEFT SIDEBAR ====================
        sidebar_widget = QWidget()
        sidebar_layout = QVBoxLayout(sidebar_widget)
        sidebar_layout.setContentsMargins(5, 5, 5, 5)

        # Search Bar Area
        search_layout = QHBoxLayout()
        self.search_input: QLineEdit = QLineEdit()
        self.search_input.setPlaceholderText("Search streams...")
        self.btn_search: QPushButton = QPushButton("⌕")
        self.btn_search.setFixedWidth(40)

        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.btn_search)
        sidebar_layout.addLayout(search_layout)

        self.stream_list_widget: QListWidget = QListWidget()
        sidebar_layout.addWidget(self.stream_list_widget)

        splitter.addWidget(sidebar_widget)

        # ==================== RIGHT VIEWING AREA ====================
        self.mdi_area: QMdiArea = QMdiArea()
        self.mdi_area.setViewMode(QMdiArea.ViewMode.TabbedView)
        self.mdi_area.setTabsClosable(True)

        splitter.addWidget(self.mdi_area)

        splitter.setSizes([250, 950])

        safe_connect(self.btn_search.clicked, self.perform_search)
        safe_connect(self.search_input.returnPressed, self.perform_search)

    # ==================== LOGIC ====================
    def perform_search(self) -> None:
        """Filters the streams based on the search input."""
        query = self.search_input.text().lower()
        self.refresh_stream_list(query=query)

    def refresh_stream_list(self, query: str = "") -> None:
        """Fetches streams and populates the list, applying a filter if requested."""
        self.stream_list_widget.clear()

        all_streams = self.manager.query_streams()

        for index, stream in all_streams:
            if query and query not in stream.name.lower():
                continue

            item = QListWidgetItem(self.stream_list_widget)
            widget = StreamListItemWidget(stream, stream_id=index)

            safe_connect(widget.launch_requested, self.start_launch_workflow)

            widget.update_status(stream.live)

            item.setSizeHint(widget.sizeHint())
            self.stream_list_widget.addItem(item)
            self.stream_list_widget.setItemWidget(item, widget)

    def start_launch_workflow(self, stream_id: int, stream: Stream) -> None:
        """STEP 1: Run status and quality checks in the background."""
        worker = LaunchPrecheckWorker(self.manager, stream_id, stream)

        safe_connect(worker.is_offline, self.on_stream_offline)
        safe_connect(worker.ready_to_launch, self.on_qualities_ready)
        safe_connect(worker.finished, lambda w=worker: self.active_workers.remove(w))  # type: ignore

        self.active_workers.append(worker)
        worker.start()

    def on_stream_offline(self, stream_name: str) -> None:
        """STEP 2 (Failed): Pop up error if stream is offline."""
        _ = QMessageBox.warning(
            self, "Stream Offline", f"The stream '{stream_name}' is currently offline."
        )

    def on_qualities_ready(
        self, available_qualities: list[str], stream_id: int, stream: Stream
    ) -> None:
        """STEP 2 (Success): Ask for quality and create window."""
        selected_quality = dialogs.ask_quality_dialog(self, available_qualities)
        if not selected_quality:
            return

        video_window = StreamVideoWindow(stream_id, stream.name, self.manager)
        _ = self.mdi_area.addSubWindow(video_window)
        video_window.show()

        win_id = video_window.get_win_id()

        def on_error_callback(_failed_stream_id: int, error_msg: str) -> None:
            sig: Any = self.stream_error_signal
            sig.emit(f"Error playing {stream.name}: {error_msg}")

        self.manager.launch_stream(
            stream_id=stream_id,
            win_id=win_id,
            quality=selected_quality,
            on_error=on_error_callback,
        )

    def show_stream_error(self, message: str) -> None:
        _ = QMessageBox.warning(self, "Playback Error", message)

    def close_all_streams(self) -> None:
        """Closes all video windows, which triggers their stop_stream logic."""
        self.mdi_area.closeAllSubWindows()
