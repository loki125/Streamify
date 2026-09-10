from __future__ import annotations

import os

from PyQt6.QtWidgets import QApplication

JSON_EDIT_WARNING = """
WARNING: If you break this file, your streams will reset!\n\n
If you make changes, please restart the app to see them.\n
Do you want to proceed?
"""

JSON_EDIT_NOTE = """
Streams cleared.\n\n
If you regret this, DO NOT CLOSE STREAMIFY YET! <br>
Click 'Edit streamify.json' and manually copy your backups. <br>
Once you restart the app, the reset is permanent.
"""

TWITCH_IMPORT_HELP = """
<b>What are these?</b><br>
To read your private follows, Twitch requires authentication.<br>
You can extract these from your browser cookies/dev tools while logged into Twitch.<br><br>
<i>Note: Streamify does NOT save these in memory or to disk for your privacy.
They are used once and immediately destroyed.</i>
"""


def load_stylesheet(app: QApplication, theme_name: str = "dark") -> None:
    """Loads a CSS file from the styles directory and applies it to the app."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    style_path = os.path.join(base_dir, "styles", f"{theme_name}.css")

    if os.path.exists(style_path):
        with open(style_path, "r") as f:
            app.setStyleSheet(f.read())
    else:
        print(f"Warning: Stylesheet {style_path} not found.")
