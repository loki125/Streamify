import concurrent.futures
import json
import os
import re
import subprocess
from typing import Dict, List

from streamlink.session.session import Streamlink

from .config import DEFAULT_PLAYER, FAVORITES_FILE
from .models import Stream


class StreamlinkManager:
    def __init__(self, favorites_path=FAVORITES_FILE, player=DEFAULT_PLAYER):
        self.favorites_path = favorites_path
        self.player = player
        self.session = Streamlink()

        self.current_process = None
        self.active_stream_idx = None

        self._raw_data = self._read_or_create_json()

        self.streams: List[Stream] = self.load_streams()
        self.categorys: Dict[str, int] = self.load_categorys()
        self.urls: Dict[str, int] = self.load_urls()

    def _read_or_create_json(self):
        if not os.path.exists(self.favorites_path):
            os.makedirs(os.path.dirname(self.favorites_path), exist_ok=True)
            default_data = {
                "streams": [],
                "urls": ["twitch.tv"],
                "categorys": ["Gaming", "Just Chatting", "General"],
            }
            with open(self.favorites_path, "w") as f:
                json.dump(default_data, f, indent=4)
            return default_data

        with open(self.favorites_path, "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {"streams": [], "urls": ["twitch.tv"], "categorys": ["General"]}

    def load_streams(self) -> List[Stream]:
        raw_streams = self._raw_data.get("streams", [])
        return [Stream(**s) for s in raw_streams]

    def load_categorys(self) -> Dict[str, int]:
        raw_cats = self._raw_data.get("categorys", [])
        return {cat: idx for idx, cat in enumerate(raw_cats)}

    def load_urls(self) -> Dict[str, int]:
        raw_urls = self._raw_data.get("urls", [])
        return {url: idx for idx, url in enumerate(raw_urls)}

    def save_favorites(self):
        cat_list = [""] * len(self.categorys)
        for k, v in self.categorys.items():
            cat_list[v] = k

        url_list = [""] * len(self.urls)
        for k, v in self.urls.items():
            url_list[v] = k

        data = {
            "streams": [
                {"name": s.name, "url_id": s.url_id, "category_id": s.category_id}
                for s in self.streams
            ],
            "urls": url_list,
            "categorys": cat_list,
        }

        with open(self.favorites_path, "w") as f:
            json.dump(data, f, indent=4)

    def add_stream(self, stream: Stream):
        self.streams.append(stream)
        self.save_favorites()

    def delete_stream(self, idx):
        if 0 <= idx < len(self.streams):
            if self.active_stream_idx == idx:
                self.stop_stream()
            self.streams.pop(idx)
            self.save_favorites()

    def launch_stream(self, idx, quality="best", wid=None):
        self.stop_stream()

        if 0 <= idx < len(self.streams):
            stream = self.streams[idx]
            url_str = self.get_url_by_id(stream.url_id)
            full_url = f"https://{url_str}/{stream.name}"

            player_args = f"--wid={wid} {{filename}}" if wid else "{filename}"
            cmd = [
                "streamlink",
                full_url,
                quality,
                "--player",
                self.player,
                "-a",
                player_args,
            ]

            self.current_process = subprocess.Popen(
                cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
            self.active_stream_idx = idx

    def stop_stream(self):
        if self.current_process is not None:
            self.current_process.terminate()
            self.current_process = None
        self.active_stream_idx = None

    def add_category(self, name):
        if name and name not in self.categorys:
            self.categorys[name] = len(self.categorys)
            self.save_favorites()

    def delete_category(self, name):
        if name in self.categorys:
            del self.categorys[name]
            self.categorys = {k: i for i, k in enumerate(self.categorys.keys())}
            self.save_favorites()

    def add_url(self, url):
        if url not in self.urls:
            self.urls[url] = len(self.urls)
            self.save_favorites()

    def search_streams(self, name, category):
        results = []
        name_pattern = re.compile(name, re.IGNORECASE) if name else None

        for idx, s in enumerate(self.streams):
            cat_str = self.get_category_by_id(s.category_id)
            if category and category != "All" and cat_str != category:
                continue
            if name_pattern and not name_pattern.search(s.name):
                continue
            results.append((idx, s))

        return results

    def check_statuses_once(self, update_callback):
        def check_single(stream):
            status = "Offline"
            try:
                url_str = self.get_url_by_id(stream.url_id)
                full_url = f"https://{url_str}/{stream.name}"
                streams = self.session.streams(full_url)
                if streams:
                    status = "Live"
            except Exception:
                status = "Error"
            update_callback(stream, status)

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            for stream in self.streams:
                executor.submit(check_single, stream)

    def get_url_by_id(self, url_id: int) -> str:
        for k, v in self.urls.items():
            if v == url_id:
                return k
        return ""

    def get_category_by_id(self, cat_id: int) -> str:
        for k, v in self.categorys.items():
            if v == cat_id:
                return k
        return ""
