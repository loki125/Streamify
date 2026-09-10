from __future__ import annotations

from dataclasses import dataclass, field
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


class Theme(Enum):
    dark = "dark"
    light = "light"


@dataclass
class CustomSettings:
    chat_active: bool = False
    pause_start_key: str = "space"
    mute_unmute_key: str = "m"
    volume_num: int = 50

    @classmethod
    def default(cls, settings: Settings) -> CustomSettings:
        return cls(
            chat_active=settings.default_chat_active,
            pause_start_key=settings.default_pause_start_key,
            mute_unmute_key=settings.default_mute_unmute_key,
            volume_num=settings.default_volume_num,
        )

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CustomSettings:
        return cls(
            chat_active=data.get("chat_active", False),
            pause_start_key=data.get("pause_start_key", "space"),
            mute_unmute_key=data.get("mute_unmute_key", "m"),
            volume_num=data.get("volume_num", 50),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "chat_active": self.chat_active,
            "pause_start_key": self.pause_start_key,
            "mute_unmute_key": self.mute_unmute_key,
            "volume_num": self.volume_num,
        }


@dataclass
class Settings:
    default_chat_active: bool = False
    default_pause_start_key: str = "space"
    default_mute_unmute_key: str = "m"
    default_volume_num: int = 50
    dark_light_mode: Theme = Theme.dark
    auto_select_quality: tuple[Quality, bool] = (Quality.best, False)
    auto_refresh_sec: float = 60.0
    custom_settings: dict[int, CustomSettings] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Settings:
        raw_custom = data.get("custom_settings", {})
        custom_settings = {
            int(k): CustomSettings.from_dict(v) for k, v in raw_custom.items()
        }

        raw_quality = data.get("auto_select_quality", ["best", False])

        return cls(
            default_chat_active=data.get("default_chat_active", False),
            default_pause_start_key=data.get("default_pause_start_key", "space"),
            default_mute_unmute_key=data.get("default_mute_unmute_key", "m"),
            default_volume_num=data.get("default_volume_num", 50),
            dark_light_mode=Theme(data.get("dark_light_mode", "dark")),
            auto_select_quality=(Quality(raw_quality[0]), raw_quality[1]),
            auto_refresh_sec=data.get("auto_refresh_sec", 60.0),
            custom_settings=custom_settings,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "default_chat_active": self.default_chat_active,
            "default_pause_start_key": self.default_pause_start_key,
            "default_mute_unmute_key": self.default_mute_unmute_key,
            "default_volume_num": self.default_volume_num,
            "dark_light_mode": self.dark_light_mode.value,
            "auto_select_quality": (
                self.auto_select_quality[0].value,
                self.auto_select_quality[1],
            ),
            "auto_refresh_sec": self.auto_refresh_sec,
            "custom_settings": {
                str(k): v.to_dict() for k, v in self.custom_settings.items()
            },
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
            live=False,
        )

    def to_dict(self) -> dict[str, Any]:
        return {"name": self.name, "url": self.url, "category_id": self.category_id}


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

    def to_dict(self) -> dict[str, Any]:
        return {
            STREAM_KEY_NAME: [s.to_dict() for s in self.streams],
            CATEGORIES_KEY_NAME: self.categories,
        }
