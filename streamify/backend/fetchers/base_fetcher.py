from abc import ABC
from typing import Any


class BaseFetcher(ABC):
    """Abstract Base Class that all platform fetchers must inherit from."""

    @abstractmethod
    def fetch_follows(self) -> list[dict[str, Any]]:
        """Fetch and return the list of followed accounts/channels."""
        pass
