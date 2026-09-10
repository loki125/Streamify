# pyright: reportUnknownMemberType=none
from __future__ import annotations

from typing import Any

from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QBrush, QColor
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
from ..utils.dialogs import StreamEditDialog
from ..utils.signals import (
    GlobalStatusWorker,
    LaunchPrecheckWorker,
    SingleStatusWorker,
    safe_connect,
)
from ..utils.widgets import StreamListItemWidget, StreamVideoWindow


class HomeTab(QWidget):
    stream_error_signal: pyqtSignal = pyqtSignal(str)

    def __init__(
        self, manager: StreamlinkManager, settings_config: SettingsConfig
    ) -> None:
        super().__init__()
        self.manager: StreamlinkManager = manager
        self.settings_config: SettingsConfig = settings_config

        self.active_workers: list[QThread] = []

        safe_connect(self.stream_error_signal, self.show_stream_error)
        self.init_ui()
        self.refresh_stream_list()

    def init_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.splitter: QSplitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(self.splitter)

        # ==================== LEFT SIDEBAR ====================
        self.sidebar_widget: QWidget = QWidget(self.splitter)
        sidebar_layout = QVBoxLayout(self.sidebar_widget)
        sidebar_layout.setContentsMargins(5, 5, 5, 5)

        search_layout = QHBoxLayout()
        self.search_input: QLineEdit = QLineEdit()
        self.search_input.setPlaceholderText("⌕ Search streams...")

        self.btn_refresh: QPushButton = QPushButton("↻")
        self.btn_refresh.setFixedWidth(40)

        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.btn_refresh)
        sidebar_layout.addLayout(search_layout)

        self.stream_list_widget: QListWidget = QListWidget()
        sidebar_layout.addWidget(self.stream_list_widget)

        self.btn_add_stream: QPushButton = QPushButton("✚")
        self.btn_add_stream.setToolTip("Add new stream")
        sidebar_layout.addWidget(self.btn_add_stream)

        safe_connect(self.btn_refresh.clicked, self.trigger_global_status_check)
        safe_connect(self.btn_add_stream.clicked, self.open_add_dialog)

        # ==================== RIGHT VIEWING AREA ====================
        self.mdi_area: QMdiArea = QMdiArea(self.splitter)
        self.mdi_area.setViewMode(QMdiArea.ViewMode.TabbedView)
        self.mdi_area.setTabsClosable(True)

        self.mdi_area.setBackground(QBrush(QColor("#0e0e10")))

        self.splitter.addWidget(self.mdi_area)

        self.splitter.setSizes([250, 950])

        safe_connect(self.search_input.textChanged, self.refresh_stream_list)

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
            safe_connect(widget.edit_requested, self.open_edit_dialog)
            safe_connect(
                widget.status_check_requested, self.trigger_single_status_check
            )
            safe_connect(widget.remove_requested, self.remove_stream)
            safe_connect(
                widget.custom_settings_requested, self.open_custom_settings_dialog
            )

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
        for sub_window in self.mdi_area.subWindowList():
            if (
                isinstance(sub_window, StreamVideoWindow)
                and sub_window.stream_id == stream_id
            ):
                self.mdi_area.setActiveSubWindow(sub_window)
                return

        selected_quality = dialogs.ask_quality_dialog(self, available_qualities)
        if not selected_quality:
            return

        video_window = StreamVideoWindow(stream_id, stream.name, self.manager)
        _ = self.mdi_area.addSubWindow(video_window)

        video_window.showMaximized()

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

    def _resolve_category_id(self, category_str: str) -> int:
        """Helper to convert string to ID, creating a new category if needed."""
        if not category_str:
            return 0

        cats = self.manager.get_all_categories()
        if category_str in cats:
            return cats.index(category_str)

        self.manager.add_category(category_str)
        new_cats = self.manager.get_all_categories()
        return new_cats.index(category_str)

    def open_add_dialog(self) -> None:
        dialog = StreamEditDialog(self, self.manager)
        if dialog.exec():
            name, url, category_str = dialog.get_data()
            if name and url:
                cat_id = self._resolve_category_id(category_str)

                stream_id = self.manager.add_stream(name, url, cat_id)
                self.refresh_stream_list()

                new_stream = self.manager.get_stream(stream_id)
                if new_stream is None:
                    raise ValueError(f"Ghost stream with id {stream_id}")

                self.trigger_single_status_check(stream_id, new_stream)

    def open_edit_dialog(self, stream_id: int, stream: Stream) -> None:
        dialog = StreamEditDialog(self, self.manager, stream)
        if dialog.exec():
            name, url, category_str = dialog.get_data()
            if name and url:
                cat_id = self._resolve_category_id(category_str)
                self.manager.update_stream(stream_id, name, url, cat_id)
                self.refresh_stream_list()

    def remove_stream(self, stream_id: int, _stream: Stream) -> None:
        self.manager.remove_stream(stream_id)
        self.refresh_stream_list()

    def open_custom_settings_dialog(self, stream_id: int, _stream: Stream) -> None:
        settings = self.settings_config.get_settings()
        current_custom = settings.custom_settings.get(stream_id)

        dialog = dialogs.CustomStreamSettingsDialog(self, current_custom, settings)

        if dialog.exec():
            new_custom = dialog.get_custom_settings()
            settings.custom_settings[stream_id] = new_custom
            self.settings_config.save_settings(settings)

    # --- STATUS CHECKING ---

    def trigger_global_status_check(self) -> None:
        self.btn_refresh.setEnabled(False)

        worker = GlobalStatusWorker(self.manager)
        self.active_workers.append(worker)

        safe_connect(worker.checked_finished, self.on_global_statuses_checked)
        safe_connect(
            worker.checked_finished,
            lambda: (
                self.worker_cleanup(worker),
                self.btn_refresh.setEnabled(True),
            ),
        )
        worker.start()

    def on_global_statuses_checked(self, statuses: dict[int, bool]) -> None:
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

    def trigger_single_status_check(self, stream_id: int, stream: Stream) -> None:
        """Handles Right-Click -> Check Status."""
        worker = SingleStatusWorker(self.manager, stream_id, stream)
        self.active_workers.append(worker)

        safe_connect(worker.checked_finished, self.on_single_status_checked)

        safe_connect(worker.checked_finished, self.worker_cleanup)
        worker.start()

    def on_single_status_checked(self, stream_id: int, is_live: bool) -> None:
        """Saves status to backend and updates that one specific dot."""
        _ = self.manager.set_single_status(stream_id, is_live)

        for i in range(self.stream_list_widget.count()):
            item = self.stream_list_widget.item(i)
            if item is None:
                continue

            widget = self.stream_list_widget.itemWidget(item)
            if (
                isinstance(widget, StreamListItemWidget)
                and widget.stream_id == stream_id
            ):
                widget.update_status(is_live)
                break

    def worker_cleanup(self, worker: QThread) -> None:
        if worker in self.active_workers:
            self.active_workers.remove(worker)
