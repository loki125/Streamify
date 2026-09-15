from __future__ import annotations

from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any, cast, override
from urllib.parse import parse_qs, urlparse

from .config import (
    TWITCH_AUTH_REDIRECT_HTML,
    TWITCH_AUTH_SUCCESS_HTML,
)


class OAuthHTTPServer(HTTPServer):
    access_token: str | None = None


class OAuthCallbackHandler(BaseHTTPRequestHandler):
    """Private Backend HTTP Server to catch the Twitch token."""

    def do_GET(self) -> None:
        parsed = urlparse(self.path)

        if parsed.path == "/":
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            _ = self.wfile.write(TWITCH_AUTH_REDIRECT_HTML.encode("utf-8"))

        elif parsed.path == "/callback":
            params = parse_qs(parsed.query)

            server = cast(OAuthHTTPServer, self.server)
            server.access_token = params.get("access_token", [None])[0]

            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            _ = self.wfile.write(TWITCH_AUTH_SUCCESS_HTML.encode("utf-8"))

    @override
    def log_message(self, format: str, *args: Any) -> None:
        pass
