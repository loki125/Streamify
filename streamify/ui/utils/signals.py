from __future__ import annotations

from typing import Any, override

from PyQt6.QtCore import QThread, pyqtSignal
from requests.exceptions import RequestException

from streamify.backend.core.models import Stream
from streamify.backend.fetchers.base_fetcher import BaseFetcher
from streamify.backend.manager import StreamlinkManager


def safe_connect(signal: Any, slot: Any) -> None:
    """Connects a PyQt signal to a slot, silencing pyright warnings."""
    signal.connect(slot)


class LaunchPrecheckWorker(QThread):
    """Handles the exact workflow: Check status -> If Live -> Check Qualities."""

    is_offline: pyqtSignal = pyqtSignal(str)
    auto_ready_to_launch: pyqtSignal = pyqtSignal(str, int, object)
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

        if not self.stream_obj.live or self.manager.check_single_status(
            self.stream_obj
        ):
            sig_off: Any = self.is_offline
            sig_off.emit(self.stream_obj.name)
            return

        qualities = self.manager.check_qualities(self.stream_id)
        self.ready_to_launch.emit(qualities, self.stream_id, self.stream_obj)


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
    fetch_finished: pyqtSignal = pyqtSignal(list)
    error: pyqtSignal = pyqtSignal(str)

    def __init__(self, fetcher: BaseFetcher) -> None:
        super().__init__()
        self.fetcher: BaseFetcher = fetcher

    @override
    def run(self) -> None:
        try:
            new_streams: list[Stream] = self.fetcher.fetch_follows()
            self.fetch_finished.emit(new_streams)
        except (ValueError, RequestException) as e:
            self.error.emit(str(e))


class PlatformAuthWorker(QThread):
    """A generic UI Thread that delegates authentication to ANY backend fetcher."""

    auth_successful: pyqtSignal = pyqtSignal(object)
    error: pyqtSignal = pyqtSignal(str)

    def __init__(self, fetcher: BaseFetcher, **auth_kwargs: Any) -> None:
        super().__init__()
        self.fetcher: BaseFetcher = fetcher
        self.auth_kwargs: Any = auth_kwargs

    @override
    def run(self) -> None:
        try:
            result = self.fetcher.authenticate(**self.auth_kwargs)

            sig: Any = self.auth_successful
            sig.emit(result)

        except (ValueError, TimeoutError, OSError, NotImplementedError) as e:
            sig_err: Any = self.error
            sig_err.emit(str(e))
