from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from .config import CATEGORIES_KEY_NAME, STREAM_KEY_NAME


class Quality(Enum):
    audio_only = "audio_only"
    _160p = "160p"
    _360p = "360p"
    _480p = "480p"
    _720p60 = "720p60"
    _1080p60 = "1080p60"
    worst = "worst"
    best = "best"


@dataclass
class Settings:
    chat_active: bool
    pause_start_key: str
    mute_unmute_key: str
    volume_num: int
    default_quality: Quality

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Settings:
        return cls(
            chat_active=data["chat_active"],
            pause_start_key=data["pause_start_key"],
            mute_unmute_key=data["mute_unmute_key"],
            volume_num=data["volume_num"],
            default_quality=Quality(data["default_quality"]),  # "best" -> Quality.best
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "chat_active": self.chat_active,
            "pause_start_key": self.pause_start_key,
            "mute_unmute_key": self.mute_unmute_key,
            "volume_num": self.volume_num,
            "default_quality": self.default_quality.value,  # Quality.best -> "best"
        }


@dataclass
class Stream:
    name: str
    url: str
    category_id: int = 0
    live: bool = False

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Stream:
        return cls(
            name=data["name"],
            url=data["url"],
            category_id=data.get("category_id", 0),
            live=data.get("live", False),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "url": self.url,
            "category_id": self.category_id,
            "live": self.live,
        }


@dataclass
class MediaCatalog:
    streams: list[Stream]
    categories: list[str]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> MediaCatalog:
        return cls(
            streams=[Stream.from_dict(s) for s in data.get(STREAM_KEY_NAME, [])],
            categories=data.get(CATEGORIES_KEY_NAME, []),
        )

    @classmethod
    def to_dict(cls) -> dict[str, Any]:
        return {
            STREAM_KEY_NAME: [s.to_dict() for s in cls.streams],
            CATEGORIES_KEY_NAME: cls.categories,
        }
