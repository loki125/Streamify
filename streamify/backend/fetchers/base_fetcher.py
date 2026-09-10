from __future__ import annotations

from abc import ABC, abstractmethod

from ..core.models import Stream


class BaseFetcher(ABC):
    """Abstract Base Class that all platform fetchers must inherit from."""

    @abstractmethod
    def fetch_follows(self) -> list[Stream]:
        """Fetch and return the list of followed accounts/channels."""
        return []

    @abstractmethod
    def check_status(self, url: str) -> bool:
        """Check the status of the fetcher (e.g., if the API key is valid)."""
        return False
