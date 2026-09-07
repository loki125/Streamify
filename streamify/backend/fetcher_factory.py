from __future__ import annotations

from typing import Any, ClassVar

from .fetchers.base_fetcher import BaseFetcher
from .fetchers.twitch_fetcher import TwitchFetcher


class FetcherFactory:
    """Factory class to generate specific platform fetchers."""

    _fetcher_registry: ClassVar[dict[str, type[BaseFetcher]]] = {
        "twitch": TwitchFetcher
    }

    @classmethod
    def get_fetcher(cls, platform: str, **kwargs: Any) -> BaseFetcher:
        """
        Instantiate a fetcher for a given platform.

        :param platform: 'twitch', etc.
        :param kwargs: Credentials and options required by the specific fetcher.
        """
        platform_key = platform.lower().strip()
        fetcher_class = cls._fetcher_registry.get(platform_key)

        if not fetcher_class:
            raise ValueError(
                f"Unknown platform '{platform}'. \nSupported platforms: {list(cls._fetcher_registry.keys())}"
            )

        return fetcher_class(**kwargs)

    @classmethod
    def register_fetcher(cls, platform_name: str, fetcher_cls: type[BaseFetcher]):
        """Allows dynamically registering new platform fetchers."""
        cls._fetcher_registry[platform_name.lower().strip()] = fetcher_cls
