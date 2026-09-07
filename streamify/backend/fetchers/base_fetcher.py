from __future__ import annotations

from abc import ABC, abstractmethod

from ..models import Stream


class BaseFetcher(ABC):
    """Abstract Base Class that all platform fetchers must inherit from."""

    @abstractmethod
    def fetch_follows(self) -> list[Stream]:
        """Fetch and return the list of followed accounts/channels."""
        return []
