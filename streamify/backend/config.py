import os

APP_NAME = "Streamify"
STREAM_LIST = os.path.expanduser(f"~/.local/share/{APP_NAME}/streams.json")
SETTINGS_FILE = os.path.expanduser(f"~/.local/share/{APP_NAME}/settings.json")
DEFAULT_PLAYER = "mpv"

STREAM_KEY_NAME = "streams"
CATEGORIES_KEY_NAME = "categories"
DEFAULT_CATEGORY = "Default"
