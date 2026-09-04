from .models import Settings


class SettingsConfig:
    def __init__(self):
        self._settings: Settings = self.fetch_settings()

    def fetch_settings(self) -> Settings:
        return Settings(
            player="",
            chat_active=False,
            pause_start_key="",
            mute_unmute_key="",
            volume_num=0,
            default_quality="",
        )

    def save_settings(self, settings: Settings) -> None:
        self._settings = settings

    def get_settings(self) -> Settings:
        return self._settings
