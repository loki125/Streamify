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
class Stream:
    name: str
    url: str
    category_id: int = 0
    live: bool = False

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Stream:
        return cls(name=data["name"], url=data["url"], category_id=data["category_id"])

    @classmethod
    def to_dict(cls) -> dict[str, Any]:
        return {
            "name": cls.name,
            "url": cls.url,
            "category_id": cls.category_id,
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
