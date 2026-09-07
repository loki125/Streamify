from __future__ import annotations

from PyQt6.QtCore.QtWidgets import QInputDialog, QMessageBox, QWidget

from streamify.backend.core.models import Quality


def ask_quality_dialog(parent: QWidget, fetched_qualities: list[str]) -> Quality | None:
    """Prompts the user for stream quality based on dynamically fetched availability."""

    valid_enum_values = [q.value for q in Quality]

    display_qualities = [q for q in fetched_qualities if q in valid_enum_values]

    if not display_qualities:
        display_qualities = ["best", "worst", "audio_only"]

    quality_str, ok = QInputDialog.getItem(
        parent, "Select Quality", "Available Qualities:", display_qualities, 0, False
    )

    if ok and quality_str:
        return Quality(quality_str)  # Converts the string back into your Enum

    return None


def ask_stream_name_dialog(parent: QWidget) -> str | None:
    """Prompts the user for a manual stream name."""
    name, ok = QInputDialog.getText(parent, "Add Stream", "Stream Name / Channel:")
    return name if ok and name else None


def confirm_stop_stream(parent: QWidget) -> bool:
    """Asks the user to confirm closing a stream."""
    reply = QMessageBox.question(
        parent,
        "Stop Stream",
        "Do you want to close this stream?",
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
    )
    return reply == QMessageBox.StandardButton.Yes


def confirm_remove_stream(parent: QWidget, stream_name: str) -> bool:
    """Asks the user to confirm removing a stream from DB."""
    reply = QMessageBox.question(
        parent,
        "Remove Stream",
        f"Remove {stream_name}?",
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
    )
    return reply == QMessageBox.StandardButton.Yes
