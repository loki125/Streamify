from __future__ import annotations

import re
import webbrowser
from typing import Any, override

import requests

from ..core.models import Stream
from .base_fetcher import BaseFetcher
from .config import (
    TWITCH_API,
    TWITCH_CLIENT_ID,
    TWITCH_URL,
)
from .models import OAuthCallbackHandler, OAuthHTTPServer


class TwitchFetcher(BaseFetcher):
    def __init__(
        self,
        client_id: str = TWITCH_CLIENT_ID,
        access_token: str | None = None,
    ):
        self.client_id: str | None = client_id
        self.access_token: str | None = access_token

    @override
    def authenticate(self, **kwargs: Any) -> str:
        """
        Authenticates via Twitch OAuth.
        Expected kwargs: `port` (int) - The localhost port for the redirect server.
        """
        port = kwargs.get("port")
        if not isinstance(port, int):
            raise TypeError(
                "TwitchFetcher.authenticate requires an integer 'port' in kwargs."
            )

        if not self.client_id:
            raise ValueError("Client ID is required for authentication.")

        server = OAuthHTTPServer(("localhost", port), OAuthCallbackHandler)
        server.access_token = None
        server.timeout = 120

        auth_url = (
            f"https://id.twitch.tv/oauth2/authorize"
            f"?client_id={self.client_id}"
            f"&redirect_uri=http://localhost:{port}"
            f"&response_type=token"
            f"&scope=user:read:follows"
        )

        _ = webbrowser.open(auth_url)

        while not getattr(server, "access_token", None):
            server.handle_request()

        if not server.access_token:
            raise TimeoutError("Authentication timed out or was canceled.")

        self.access_token = server.access_token
        return self.access_token

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
