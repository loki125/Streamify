import concurrent.futures
import json
import os
import subprocess

from streamlink.session.session import Streamlink

from .config import DEFAULT_PLAYER
from .database import StreamDB
from .models import Stream


class StreamlinkManager:
    def __init__(self, player=DEFAULT_PLAYER):
        self.player = player
        self.session = Streamlink()

        self.database = StreamDB()

    def launch_stream(self, stream_url: str):
        pass

    def stop_stream(self):
        pass

    def check_statuses(self):
        pass
