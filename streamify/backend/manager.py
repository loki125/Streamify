# pyright: reportUnknownMemberType=none
from __future__ import annotations

import threading
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from types import TracebackType
from typing import Any, Self

import mpv  # pyright: ignore[reportMissingTypeStubs]
from streamlink.exceptions import NoPluginError, PluginError, StreamlinkError
from streamlink.session.session import Streamlink

from streamify.backend.fetcher_factory import FetcherFactory

from .core.config import (
    DEFAULT_CATEGORY_ID,
    STREAMLINK_HTTP_TIMEOUT,
    STREAMLINK_SESSION_TIMEOUT,
)
from .core.database import StreamDB
from .core.models import CustomSettings, Quality, Settings, Stream
from .core.settings import SettingsConfig


class StreamlinkManager:
    def __init__(self) -> None:
        self._session: Streamlink = Streamlink()
        self._session.set_option(STREAMLINK_HTTP_TIMEOUT, STREAMLINK_SESSION_TIMEOUT)

        self._database: StreamDB = StreamDB()
        self.settings_config: SettingsConfig = SettingsConfig()

        self._active_players: dict[int, mpv.MPV] = {}

    def __enter__(self) -> Self:
        """Called when entering the 'with' block."""
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Called automatically when the app exits."""
        self.stop_all_streams()
        self._database.save_streams_json()
        self.settings_config.save_settings()

    def stop_all_streams(self) -> None:
        for player in self._active_players.values():
            player.terminate()
        self._active_players.clear()

    def construct_raw_url(self, stream_id: int, quality: Quality) -> str:
        """Fetches the raw .m3u8 video URL for a given stream ID and quality."""
        stream_obj = self._database.get_stream(stream_id)
        if stream_obj is None:
            raise ValueError(f"Stream {stream_id} not found in database")

        streams = self._session.streams(stream_obj.url)
        if not streams:
            raise ValueError(f"Stream {stream_obj.name} is currently offline")

        quality_str = str(quality.value if hasattr(quality, "value") else quality)
        target_stream: Any = streams.get(quality_str) or streams.get("best")

        if target_stream is None:
            raise ValueError(f"No usable stream found for {stream_obj.name}")

        if hasattr(target_stream, "to_url"):
            return str(target_stream.to_url())
        if hasattr(target_stream, "url"):
            return str(target_stream.url)

        raise ValueError(f"Unsupported stream format: {type(target_stream)}")

    def stream_worker(
        self,
        stream_id: int,
        win_id: int,
        quality: Quality,
        on_error: Callable[[int, str], None] | None = None,
    ) -> None:
        try:
            raw_url = self.construct_raw_url(stream_id, quality)
            settings = self.settings_config.get_settings()

            player = mpv.MPV(
                wid=str(win_id), volume_max=150, log_handler=print, panscan=1.0
            )
            self._active_players[stream_id] = player
            self.apply_settings(settings, stream_id)

            player.play(raw_url)

        except (StreamlinkError, NoPluginError, PluginError, ValueError) as e:
            if on_error:
                on_error(stream_id, f"Stream error: {e}")
        except (OSError, TimeoutError, ConnectionError) as e:
            if on_error:
                on_error(stream_id, f"Network error: {e}")

    def apply_settings(self, settings: Settings, stream_id: int) -> None:
        custom = settings.custom_settings.get(stream_id)
        if custom is None:
            custom = CustomSettings.default(settings)

        player = self._active_players[stream_id]
        if not player:
            return
        player.volume = custom.volume_num

        def format_key(qt_key: str) -> str:
            return qt_key.lower().replace(" ", "")

        @player.on_key_press(format_key(custom.pause_start_key))
        def toggle_pause() -> None:
            player.pause = not player.pause

        @player.on_key_press(format_key(custom.mute_unmute_key))
        def toggle_mute() -> None:
            player.mute = not player.mute

    def all_apply_settings(self) -> None:
        for stream_id in self._active_players:
            self.apply_settings(self.settings_config.get_settings(), stream_id)

    def toggle_pause(self, stream_id: int) -> None:
        """Toggles play/pause on the active player."""
        player = self._active_players.get(stream_id)
        if player:
            player.pause = not player.pause

    def toggle_mute(self, stream_id: int) -> None:
        """Toggles mute/unmute on the active player."""
        player = self._active_players.get(stream_id)
        if player:
            player.mute = not player.mute

    def launch_stream(
        self,
        stream_id: int,
        win_id: int,
        quality: Quality = Quality.best,
        on_error: Callable[[int, str], None] | None = None,
    ) -> None:
        thread = threading.Thread(
            target=self.stream_worker,
            args=(stream_id, win_id, quality, on_error),
            daemon=True,
        )
        thread.start()

    def stop_stream(self, stream_id: int) -> None:
        if stream_id in self._active_players:
            player = self._active_players[stream_id]
            player.stop()
            player.terminate()
            del self._active_players[stream_id]

    def check_single_status(self, stream_obj: Stream) -> bool:
        fetcher = FetcherFactory().get_fetcher_by_url(stream_obj.url)
        if fetcher is not None:
            return fetcher.check_status(stream_obj.url)

        try:
            streams = self._session.streams(stream_obj.url)
            return bool(streams)
        except (StreamlinkError, OSError):
            return False

    def set_single_status(self, stream_index: int, is_live: bool) -> bool:
        return self._database.update_stream_status(stream_index, is_live)

    def check_statuses(self) -> dict[int, bool]:
        all_streams = self._database.get_all_streams()
        changed_statuses: dict[int, bool] = {}

        with ThreadPoolExecutor(max_workers=10) as executor:
            results = executor.map(self.check_single_status, all_streams)

            for index, is_live in enumerate(results):
                if self.set_single_status(index, is_live):
                    changed_statuses[index] = True

        return changed_statuses

    def check_qualities(self, stream_id: int) -> list[str]:
        stream_obj = self._database.get_stream(stream_id)
        if not stream_obj:
            return []
        try:
            streams = self._session.streams(stream_obj.url)
            return list(streams.keys())
        except (StreamlinkError, OSError):
            return []

    def add_stream(
        self, name: str, url: str, category_id: int = DEFAULT_CATEGORY_ID
    ) -> int:
        new_stream: Stream = Stream(name=name, url=url, category_id=category_id)

        return self._database.add_stream(new_stream)

    def get_stream(self, stream_id: int) -> Stream | None:
        return self._database.get_stream(stream_id)

    def get_all_categories(self) -> list[str]:
        return self._database.get_all_categories()

    def add_category(self, category: str) -> None:
        self._database.add_category(category)

    def remove_stream(self, stream_id: int) -> None:
        _ = self._database.remove_stream(stream_id)
        if stream_id in self._active_players:
            self.stop_stream(stream_id)

    def remove_all_streams(self) -> None:
        self.stop_all_streams()
        self._database.remove_all_streams()

    def query_streams(self, query: str | None = None) -> list[tuple[int, Stream]]:
        if query is None:
            stream_list: list[tuple[int, Stream]] = [
                (i, s) for i, s in enumerate(self._database.get_all_streams())
            ]
        else:
            stream_list = self._database.search_stream(query)
        return stream_list

    def update_stream(
        self, stream_id: int, name: str, url: str, category_id: int
    ) -> None:
        stream = self._database.get_stream(stream_id)
        if stream:
            stream.name = name
            stream.url = url
            stream.category_id = category_id
