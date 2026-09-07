from __future__ import annotations

from typing import Any

from PyQt6.QtCore import QThread, pyqtSignal

from streamify.backend.core.models import Stream
from streamify.backend.fetcher_factory import FetcherFactory
from streamify.backend.manager import StreamlinkManager


class StatusCheckerWorker(QThread):
    finished: Any = pyqtSignal(dict)  # Emits dict[int, bool]

    def __init__(self, manager: StreamlinkManager) -> None:
        super().__init__()
        self.manager: StreamlinkManager = manager

    def run(self) -> None:
        statuses = self.manager.check_statuses()
        self.finished.emit(statuses)


class QualityCheckWorker(QThread):
    """Fetches available qualities in the background to prevent UI freezes."""

    finished: Any = pyqtSignal(
        list, int, object
    )  # Emits: (qualities_list, stream_id, stream_object)

    def __init__(
        self, manager: StreamlinkManager, stream_id: int, stream: Stream
    ) -> None:
        super().__init__()
        self.manager: StreamlinkManager = manager
        self.stream_id: int = stream_id  # The list index
        self.stream: Stream = stream

    def run(self) -> None:
        # Use the index directly!
        qualities = self.manager.check_qualities(self.stream_id)
        self.finished.emit(qualities, self.stream_id, self.stream)


class FetchFollowsWorker(QThread):
    finished: Any = pyqtSignal(list)  # Emits list[Stream]
    error: Any = pyqtSignal(str)

    def __init__(self, fetcher_factory: type[FetcherFactory], platform: str) -> None:
        super().__init__()
        self.fetcher_factory: type[FetcherFactory] = fetcher_factory
        self.platform: str = platform

    def run(self) -> None:
        try:
            fetcher = self.fetcher_factory.get_fetcher(self.platform)
            streams = fetcher.fetch_follows()
            self.finished.emit(streams)
        except Exception as e:
            self.error.emit(str(e))
