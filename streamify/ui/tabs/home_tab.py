# pyright: reportUnknownMemberType=none
from __future__ import annotations

from typing import Any

from PyQt6.QtCore import QSize, Qt, QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from streamify.backend.core.models import Quality, Stream
from streamify.backend.manager import StreamlinkManager

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

    def __init__(self, manager: StreamlinkManager) -> None:
        super().__init__()
        self.manager: StreamlinkManager = manager
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
        self.mdi_area: QMainWindow = QMainWindow(self.splitter)
        self.mdi_area.setWindowFlags(Qt.WindowType.Widget)
        self.mdi_area.setDockNestingEnabled(True)
        self.mdi_area.setDockOptions(
            QMainWindow.DockOption.AllowNestedDocks
            | QMainWindow.DockOption.AllowTabbedDocks
        )

        dummy = QWidget()
        dummy.setStyleSheet("background-color: #0e0e10;")
        self.mdi_area.setCentralWidget(dummy)

        self.splitter.addWidget(self.mdi_area)
        self.splitter.setSizes([250, 950])

        safe_connect(self.search_input.textChanged, self.refresh_stream_list)

    # ==================== LOGIC ====================
    def perform_search(self) -> None:
        """Filters the streams based on the search input."""
        query = self.search_input.text().lower()
        self.refresh_stream_list(query=query)

    def _create_separator_widget(self) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(10, 8, 10, 4)
        layout.setSpacing(4)

        lbl = QLabel("Offline")
        lbl.setStyleSheet(
            "color: #71717a; font-size: 11px; font-weight: bold; text-transform: uppercase;"
        )

        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet(
            "background-color: #27272a; min-height: 1px; max-height: 1px; border: none;"
        )

        layout.addWidget(lbl)
        layout.addWidget(line)
        return container

    def start_launch_override(self, stream_id: int, stream: Stream) -> None:
        self.start_launch_workflow(stream_id, stream, override=True)

    def start_launch_new(self, stream_id: int, stream: Stream) -> None:
        self.start_launch_workflow(stream_id, stream, override=False)

    def _add_stream_item(self, stream_id: int, stream: Stream) -> None:
        """Helper to create and bind a stream row item."""
        item = QListWidgetItem(self.stream_list_widget)
        widget = StreamListItemWidget(stream, stream_id=stream_id)

        safe_connect(widget.launch_override_requested, self.start_launch_override)
        safe_connect(widget.launch_new_requested, self.start_launch_new)

        safe_connect(widget.edit_requested, self.open_edit_dialog)
        safe_connect(widget.status_check_requested, self.trigger_single_status_check)
        safe_connect(widget.custom_settings_requested, self.open_custom_settings_dialog)
        safe_connect(widget.remove_requested, self.remove_stream)

        widget.update_status(stream.live)

        item.setSizeHint(QSize(widget.sizeHint().width(), 40))
        self.stream_list_widget.addItem(item)
        self.stream_list_widget.setItemWidget(item, widget)

    def refresh_stream_list(self, query: str = "") -> None:
        self.stream_list_widget.clear()
        all_streams = self.manager.query_streams()

        live_streams: list[tuple[int, Stream]] = []
        offline_streams: list[tuple[int, Stream]] = []

        for index, stream in all_streams:
            if query and query not in stream.name.lower():
                continue

            if stream.live:
                live_streams.append((index, stream))
            else:
                offline_streams.append((index, stream))

        for stream_id, stream in live_streams:
            self._add_stream_item(stream_id, stream)

        if offline_streams:
            sep_item = QListWidgetItem(self.stream_list_widget)
            sep_item.setFlags(Qt.ItemFlag.NoItemFlags)
            sep_widget = self._create_separator_widget()
            sep_item.setSizeHint(sep_widget.sizeHint())
            self.stream_list_widget.addItem(sep_item)
            self.stream_list_widget.setItemWidget(sep_item, sep_widget)

        for stream_id, stream in offline_streams:
            self._add_stream_item(stream_id, stream)

    def start_launch_workflow(
        self, stream_id: int, stream: Stream, override: bool
    ) -> None:
        worker = LaunchPrecheckWorker(self.manager, stream_id, stream, override)

        safe_connect(worker.is_offline, self.on_stream_offline)
        safe_connect(worker.ready_to_launch, self.on_qualities_ready)
        safe_connect(worker.finished, lambda w=worker: self.active_workers.remove(w))

        self.active_workers.append(worker)
        worker.start()

    def on_stream_offline(self, stream_name: str) -> None:
        _ = QMessageBox.warning(
            self, "Stream Offline", f"The stream '{stream_name}' is currently offline."
        )

    def on_qualities_ready(
        self,
        available_qualities: list[str],
        stream_id: int,
        stream: Stream,
        override: bool,
    ) -> None:
        if override:
            self.close_all_streams()
        else:
            for dock in self.mdi_area.findChildren(StreamVideoWindow):
                if dock.stream_id == stream_id:
                    dock.raise_()
                    return

        settings = self.manager.settings_config.get_settings()
        preferred_quality, auto_enabled = settings.auto_select_quality

        selected_quality: Quality | None = None

        if auto_enabled and (
            preferred_quality.value in available_qualities
            or preferred_quality == Quality.best
        ):
            selected_quality = preferred_quality
        else:
            selected_quality = dialogs.ask_quality_dialog(self, available_qualities)

        if not selected_quality:
            return

        selected_quality = dialogs.ask_quality_dialog(self, available_qualities)
        if not selected_quality:
            return

        settings = self.manager.settings_config.get_settings()
        custom = settings.custom_settings.get(stream_id)

        pause_k = custom.pause_start_key if custom else settings.default_pause_start_key
        mute_k = custom.mute_unmute_key if custom else settings.default_mute_unmute_key

        video_window = StreamVideoWindow(
            stream_id=stream_id,
            stream_name=stream.name,
            manager=self.manager,
            pause_key=pause_k,
            mute_key=mute_k,
        )
        self.mdi_area.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, video_window)
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
        for dock in self.mdi_area.findChildren(StreamVideoWindow):
            _ = dock.close()

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
        settings = self.manager.settings_config.get_settings()
        current_custom = settings.custom_settings.get(stream_id)

        dialog = dialogs.CustomStreamSettingsDialog(self, current_custom, settings)

        if dialog.exec():
            if dialog.is_reset_to_default:
                _ = settings.custom_settings.pop(stream_id, None)
            else:
                new_custom = dialog.get_custom_settings()
                settings.custom_settings[stream_id] = new_custom
            self.manager.settings_config.set_settings(settings)

            self.manager.apply_settings(settings, stream_id)

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

    def trigger_single_status_check(self, stream_id: int, stream: Stream) -> None:
        worker = SingleStatusWorker(self.manager, stream_id, stream)
        self.active_workers.append(worker)

        safe_connect(worker.checked_finished, self.on_single_status_checked)

        safe_connect(worker.checked_finished, self.worker_cleanup)
        worker.start()

    def on_global_statuses_checked(self, statuses: dict[int, bool]) -> None:
        """Updates in-memory state and re-sorts the entire list."""
        self.btn_refresh.setEnabled(True)

        for stream_id, is_live in statuses.items():
            _ = self.manager.set_single_status(stream_id, is_live)

        self.refresh_stream_list(self.search_input.text().lower())

    def on_single_status_checked(self, stream_id: int, is_live: bool) -> None:
        """Updates one stream's status and re-sorts."""
        if self.manager.set_single_status(stream_id, is_live):
            self.refresh_stream_list(self.search_input.text().lower())

    def worker_cleanup(self, worker: QThread) -> None:
        if worker in self.active_workers:
            self.active_workers.remove(worker)
