from abc import ABC, abstractmethod
from typing import Any

import requests


class TwitchFetcher(BaseFetcher):
    BASE_URL = "https://api.twitch.tv/helix"

    def __init__(
        self, client_id: str, access_token: str, user_id: str | None = None
    ):
        """
        :param client_id: Twitch App Client ID
        :param access_token: User OAuth Access Token (with 'user:read:follows' scope)
        :param user_id: (Optional) If omitted, it will automatically query the token's owner.
        """
        self.client_id = client_id
        self.access_token = access_token
        self.headers = {
            "Client-Id": self.client_id,
            "Authorization": f"Bearer {self.access_token}",
        }
        # Resolve user_id if not explicitly passed
        self.user_id = user_id or self._get_current_user_id()

    def _get_current_user_id(self) -> str:
        """Helper to get the user_id associated with the access_token."""
        url = f"{self.BASE_URL}/users"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        data = response.json().get("data", [])
        if not data:
            raise ValueError("Could not find user associated with this access token.")
        return data[0]["id"]

    def fetch_follows(self) -> List[Dict[str, Any]]:
        """
        Fetches all channels the user follows.
        Handles cursor pagination automatically to get the full list.
        """
        follows: List[Dict[str, Any]] = []
        cursor: Optional[str] = None
        url = f"{self.BASE_URL}/channels/followed"

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
            for item in data:
                follows.append(
                    {
                        "broadcaster_id": item.get("broadcaster_id"),
                        "broadcaster_login": item.get("broadcaster_login"),
                        "broadcaster_name": item.get("broadcaster_name"),
                        "followed_at": item.get("followed_at"),
                    }
                )

            # Check if there is another page of follows
            cursor = payload.get("pagination", {}).get("cursor")
            if not cursor or not data:
                break

        return follows
