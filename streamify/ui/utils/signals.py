from __future__ import annotations

from typing import Any, override

from PyQt6.QtCore import QThread, pyqtSignal

from streamify.backend.core.models import Stream
from streamify.backend.fetchers.base_fetcher import BaseFetcher
from streamify.backend.manager import StreamlinkManager


def safe_connect(signal: Any, slot: Any) -> None:
    """Connects a PyQt signal to a slot, silencing pyright warnings."""
    signal.connect(slot)


class LaunchPrecheckWorker(QThread):
    """Handles the exact workflow: Check status -> If Live -> Check Qualities."""

    is_offline: pyqtSignal = pyqtSignal(str)
    ready_to_launch: pyqtSignal = pyqtSignal(list, int, object)

    def __init__(
        self, manager: StreamlinkManager, stream_id: int, stream_obj: Stream
    ) -> None:
        super().__init__()
        self.manager: StreamlinkManager = manager
        self.stream_id: int = stream_id
        self.stream_obj: Stream = stream_obj

    @override
    def run(self) -> None:
        is_live = self.manager.check_single_status(self.stream_obj)

        if not is_live:
            sig_off: Any = self.is_offline
            sig_off.emit(self.stream_obj.name)
            return

        qualities = self.manager.check_qualities(self.stream_id)

        sig_ready: Any = self.ready_to_launch
        sig_ready.emit(qualities, self.stream_id, self.stream_obj)


class GlobalStatusWorker(QThread):
    """Checks the status of all streams (for the refresh button)."""

    checked_finished: pyqtSignal = pyqtSignal(dict)

    def __init__(self, manager: StreamlinkManager) -> None:
        super().__init__()
        self.manager: StreamlinkManager = manager

    @override
    def run(self) -> None:
        statuses = self.manager.check_statuses()
        self.checked_finished.emit(statuses)


class SingleStatusWorker(QThread):
    """Checks the status of a single stream (from right-click menu)."""

    checked_finished: pyqtSignal = pyqtSignal(int, bool)

    def __init__(
        self, manager: StreamlinkManager, stream_id: int, stream_obj: Any
    ) -> None:
        super().__init__()
        self.manager: StreamlinkManager = manager
        self.stream_id: int = stream_id
        self.stream_obj: Stream = stream_obj

    @override
    def run(self) -> None:
        is_live = self.manager.check_single_status(self.stream_obj)
        self.checked_finished.emit(self.stream_id, is_live)


class FetchFollowsWorker(QThread):
    error: pyqtSignal = pyqtSignal(str)

    def __init__(self, fetcher: BaseFetcher) -> None:
        super().__init__()
        self.fetcher: BaseFetcher = fetcher

    @override
    def run(self) -> None:
        pass
