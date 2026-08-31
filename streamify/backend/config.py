import os

APP_NAME = "Streamify"
STREAM_LIST = os.path.expanduser(f"~/.local/share/{APP_NAME}/streamify.json")
DEFAULT_PLAYER = "mpv"

STREAM_KEY_NAME = "streams"
CATEGORIES_KEY_NAME = "categories"
DEFAULT_CATEGORY = "Default"
