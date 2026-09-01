from __future__ import annotations

import threading

import mpv
from streamlink.session.session import Streamlink

from .config import DEFAULT_PLAYER
from .database import StreamDB
from .models import Quality, Stream


class StreamlinkManager:
    def __init__(self, player: str = DEFAULT_PLAYER):
        self.player: str = player
        self.session: Streamlink = Streamlink()

        self.database: StreamDB = StreamDB()
        self.active_players: dict[int, int] = {}

    def stream_worker(self):
        pass

    def construct_raw_url(self, stream_id: int, quality: Quality) -> str:
        stream_obj = self.database.get_stream(stream_id)
        if stream_obj is None:
            raise ValueError(f"Stream {stream_id} not found")

        stream = self.session.streams(stream_obj.url)
        return stream[str(quality)].to_url()

    def launch_stream(self):
        pass

    def stop_stream(self):
        pass

    def check_statuses(self):
        pass

    def check_qualities(self, stream_id: int) -> list[Quality]:
        return list(Quality)

    def get_twitch_followers(
        self,
        oAuth_token: str,
    ) -> list[Stream]:
        pass
