from __future__ import annotations

import threading
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Callable

import mpv  # pyright: ignore[reportMissingTypeStubs]
from streamlink.exceptions import NoPluginError, PluginError, StreamlinkError
from streamlink.session.session import Streamlink

from .config import DEFAULT_PLAYER
from .database import StreamDB
from .models import Quality, Stream


class StreamlinkManager:
    def __init__(self, player: str = DEFAULT_PLAYER) -> None:
        self.player_type: str = player
        self.session: Streamlink = Streamlink()
        self.database: StreamDB = StreamDB()

        self.active_players: dict[int, mpv.MPV] = {}

    def construct_raw_url(self, stream_id: int, quality: Quality) -> str:
        """Fetches the raw .m3u8 video URL for a given stream ID and quality."""
        stream_obj = self.database.get_stream(stream_id)
        if stream_obj is None:
            raise ValueError(f"Stream {stream_id} not found in database")

        streams = self.session.streams(stream_obj.url)
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

            player = mpv.MPV(wid=str(win_id), log_handler=print)
            self.active_players[stream_id] = player

            player.play(raw_url)

        except (StreamlinkError, NoPluginError, PluginError, ValueError) as e:
            if on_error:
                on_error(stream_id, f"Stream error: {e}")
        except (OSError, TimeoutError, ConnectionError) as e:
            if on_error:
                on_error(stream_id, f"Network error: {e}")

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
        if stream_id in self.active_players:
            player = self.active_players[stream_id]
            player.stop()
            player.terminate()
            del self.active_players[stream_id]

    def _check_single_status(self, stream_obj: Stream) -> bool:
        try:
            streams = self.session.streams(stream_obj.url)
            return bool(streams)
        except (StreamlinkError, OSError):
            return False

    def check_statuses(self) -> dict[int, bool]:
        all_streams = self.database.get_all_streams()
        changed_statuses: dict[int, bool] = {}

        with ThreadPoolExecutor(max_workers=10) as executor:
            results = executor.map(self._check_single_status, all_streams)

            for index, is_live in enumerate(results):
                if self.database.update_stream_status(index, is_live):
                    changed_statuses[index] = True

        return changed_statuses

    def check_qualities(self, stream_id: int) -> list[str]:
        stream_obj = self.database.get_stream(stream_id)
        if not stream_obj:
            return []
        try:
            streams = self.session.streams(stream_obj.url)
            return list(streams.keys())
        except (StreamlinkError, OSError):
            return []

    def get_twitch_followers(self, oAuth_token: str) -> list[Stream]:
        """Placeholder for Twitch Helix API integration."""
        return []
