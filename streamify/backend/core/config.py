import os

APP_NAME = "Streamify"
STREAM_LIST: str = os.path.expanduser(f"~/.local/share/{APP_NAME}/streamify.json")
SETTINGS_FILE: str = os.path.expanduser(f"~/.local/share/{APP_NAME}/settings.json")

STREAM_KEY_NAME = "streams"
CATEGORIES_KEY_NAME = "categories"
DEFAULT_CATEGORY = "Default"
DEFAULT_CATEGORY_ID = 0
