from __future__ import annotations

from typing import Any, override

import requests

from ..core.models import Stream
from .base_fetcher import BaseFetcher

TWITCH_API = "https://api.twitch.tv/helix"
TWITCH_URL = "https://www.twitch.tv"


class TwitchFetcher(BaseFetcher):
    def __init__(self, client_id: str, access_token: str, user_id: str | None = None):
        """
        :param client_id: Twitch App Client ID
        :param access_token: User OAuth Access Token (with 'user:read:follows' scope)
        :param user_id: (Optional) If omitted, it will automatically query the token's owner.
        """
        self.client_id: str = client_id
        self.access_token: str = access_token
        self.headers: dict[str, str] = {
            "Client-Id": self.client_id,
            "Authorization": f"Bearer {self.access_token}",
        }
        self.user_id: str | None = user_id or self._get_current_user_id()

    def _get_current_user_id(self) -> str:
        """Helper to get the user_id associated with the access_token."""
        url = f"{TWITCH_API}/users"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        data = response.json().get("data", [])
        if not data:
            raise ValueError("Could not find user associated with this access token.")
        return data[0]["id"]

    def _parse_data(self, data: list[dict[str, Any]]) -> list[Stream]:
        follows: list[Stream] = []
        for item in data:
            login = item.get("broadcaster_login", "")
            name = item.get("broadcaster_name") or login
            url = f"{TWITCH_URL}/{login}"

            follows.append(
                Stream(
                    name=name,
                    url=url,
                )
            )
        return follows

    @override
    def fetch_follows(self) -> list[Stream]:
        """
        Fetches all channels the user follows.
        Handles cursor pagination automatically to get the full list.
        """
        follows: list[Stream] = []
        cursor: str | None = None
        url = f"{TWITCH_API}/channels/followed"

        while True:
            params = {
                "user_id": self.user_id,
                "first": 100,  # 100 is the max allowed per page
            }
            if cursor:
                params["after"] = cursor

            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            payload = response.json()

            data = payload.get("data", [])
            follows.extend(self._parse_data(data))

            # Check if there is another page of follows
            cursor = payload.get("pagination", {}).get("cursor")
            if not cursor or not data:
                break

        return follows
