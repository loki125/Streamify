from __future__ import annotations

import importlib.resources

from PyQt6.QtWidgets import QApplication


def load_stylesheet(app: QApplication, theme_name: str = "dark") -> None:
    """Safely loads a CSS stylesheet from the installed package data."""
    try:
        # Traverses directly into the installed streamify.ui.styles directory
        styles_dir = importlib.resources.files("streamify.ui") / "styles"
        css_file = styles_dir / f"{theme_name}.css"

        if css_file.is_file():
            app.setStyleSheet(css_file.read_text(encoding="utf-8"))
        else:
            print(f"Warning: Stylesheet '{theme_name}.css' not found.")
    except Exception as e:
        print(f"Warning: Failed to load stylesheet: {e}")
