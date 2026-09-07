from __future__ import annotations

import os

from PyQt6.QtCore.QtWidgets import QApplication


def load_stylesheet(app: QApplication, theme_name: str = "dark") -> None:
    """Loads a CSS file from the styles directory and applies it to the app."""
    # Calculates path relative to this config.py file: ui/utils/../styles/theme.css
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    style_path = os.path.join(base_dir, "styles", f"{theme_name}.css")

    if os.path.exists(style_path):
        with open(style_path, "r") as f:
            app.setStyleSheet(f.read())
    else:
        print(f"Warning: Stylesheet {style_path} not found.")
