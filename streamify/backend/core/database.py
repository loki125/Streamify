from __future__ import annotations

import json
import os
import re

from .config import DEFAULT_CATEGORY, STREAM_LIST
from .models import MediaCatalog, Stream


class StreamDB:
    def __init__(self):
        self._media_cat: MediaCatalog = self.load_streams_json()

    def load_streams_json(self) -> MediaCatalog:
        if os.path.exists(STREAM_LIST):
            media_cat: MediaCatalog
            with open(STREAM_LIST, "r") as f:
                json_data = json.load(f)
                media_cat = MediaCatalog.from_dict(json_data)
        else:
            media_cat = self.init_streams_json()
        return media_cat

    def init_streams_json(self) -> MediaCatalog:
        defualt_catalog = MediaCatalog(streams=[], categories=[DEFAULT_CATEGORY])
        if not os.path.exists(STREAM_LIST):
            with open(STREAM_LIST, "w") as data:
                json.dump(defualt_catalog.to_dict(), data)

        return defualt_catalog

    def save_streams_json(self):
        if not os.path.exists(STREAM_LIST):
            with open(STREAM_LIST, "w") as data:
                json.dump(self._media_cat.to_dict(), data)

    def add_stream(self, stream: Stream) -> int:
        self._media_cat.streams.append(stream)

        return len(self._media_cat.streams)

    def remove_stream(self, stream_index: int) -> Stream | None:
        try:
            stream = self._media_cat.streams.pop(stream_index)
            return stream
        except IndexError:
            return None

    def add_category(self, category: str):
        self._media_cat.categories.append(category)

    def remove_category(self, category: str) -> bool:
        try:
            self._media_cat.categories.remove(category)
            return True
        except ValueError:
            return False

    def search_stream(self, query: str) -> list[Stream]:
        results = []
        query_pattern = re.compile(query, re.IGNORECASE) if query else None

        for idx, s in enumerate(self._media_cat.streams):
            if query_pattern and not query_pattern.search(s.name):
                continue
            results.append((idx, s))

        return results

    def get_stream(self, stream_id: int) -> Stream | None:
        return (
            self._media_cat.streams[stream_id]
            if 0 <= stream_id < len(self._media_cat.streams)
            else None
        )

    def get_all_streams(self) -> list[Stream]:
        return self._media_cat.streams

    def update_stream_status(self, stream_id: int, is_live: bool) -> bool:
        if 0 <= stream_id < len(self._media_cat.streams):
            current_status = self._media_cat.streams[stream_id].live
            if current_status != is_live:
                self._media_cat.streams[stream_id].live = is_live
                return True
        return False
