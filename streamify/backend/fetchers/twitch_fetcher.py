from __future__ import annotations

import re
from typing import Any, override

import requests

from ..core.models import Stream
from .base_fetcher import BaseFetcher

TWITCH_API = "https://api.twitch.tv/helix"
TWITCH_URL = "https://www.twitch.tv"


class TwitchFetcher(BaseFetcher):
    def __init__(
        self,
        client_id: str | None = None,
        access_token: str | None = None,
    ):
        """
        :param client_id: Twitch App Client ID
        :param access_token: User OAuth Access Token (with 'user:read:follows' scope)
        :param user_id: (Optional) If omitted, it will automatically query the token's owner.
        """

        self.client_id: str | None = client_id
        self.access_token: str | None = access_token

    @override
    def fetch_follows(self) -> list[Stream]:
        """
        Fetches all channels the user follows.
        Handles cursor pagination automatically to get the full list.
        """
        if self.client_id is None or self.access_token is None:
            raise ValueError(
                "Either client_id or access_token must be provided to fetch follows."
            )

        follows: list[Stream] = []
        cursor: str | None = None
        url = f"{TWITCH_API}/channels/followed"

        headers: dict[str, str] = {
            "Client-Id": self.client_id,
            "Authorization": f"Bearer {self.access_token}",
        }

        user_id: str | None = self._get_current_user_id(headers)
        if user_id is None:
            return []

        while True:
            params = {
                "user_id": user_id,
                "first": 100,
            }
            if cursor:
                params["after"] = cursor

            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            payload = response.json()

            data = payload.get("data", [])
            follows.extend(self._parse_data(data))

            cursor = payload.get("pagination", {}).get("cursor")
            if not cursor or not data:
                break

        return follows

    @override
    def check_status(self, url: str) -> bool:
        match = re.search(r"twitch\.tv/([a-zA-Z0-9_]+)", url)
        if match:
            channel = match.group(1)
            headers = {
                "Client-ID": "kimne78kx3ncx6brgo4mv6wki5h1ko",
            }
            payload = {
                "query": f'query {{ user(login: "{channel}") {{ stream {{ type }} }} }}'
            }

            resp = requests.post(
                "https://gql.twitch.tv/gql",
                json=payload,
                headers=headers,
                timeout=3,
            )
            data = resp.json()

            user_data = data.get("data", {}).get("user")

            return not (not user_data or not user_data.get("stream"))
        else:
            raise ValueError("[TwitchFetcher] Invalid URL")

    def _get_current_user_id(self, headers: dict[str, str]) -> str | None:
        """Helper to get the user_id associated with the access_token."""
        url = f"{TWITCH_API}/users"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json().get("data", [])
        if not data:
            return None
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
