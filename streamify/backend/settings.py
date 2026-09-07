from __future__ import annotations

import json
from pathlib import Path

from .core.config import SETTINGS_FILE
from .core.models import Quality, Settings


class SettingsConfig:
    def __init__(self) -> None:
        self.file_path: Path = Path(SETTINGS_FILE)
        self._settings: Settings = self.fetch_settings()

    def get_default_settings(self) -> Settings:
        """Returns the fallback settings."""
        return Settings(
            chat_active=False,
            pause_start_key="",
            mute_unmute_key="",
            volume_num=0,
            default_quality=Quality.best,
        )

    def fetch_settings(self) -> Settings:
        """Loads settings from file if it exists, otherwise returns defaults."""
        if not self.file_path.exists():
            return self.get_default_settings()

        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return Settings.from_dict(data)
        except (json.JSONDecodeError, OSError, ValueError, KeyError):
            return self.get_default_settings()

    def save_settings(self, settings: Settings | None = None) -> None:
        """Updates current settings (if provided) and writes to disk."""
        if settings is not None:
            self.set_settings(settings)

        self.file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(self._settings.to_dict(), f, indent=4)

    def set_settings(self, settings: Settings) -> None:
        self._settings = settings

    def get_settings(self) -> Settings:
        return self._settings
