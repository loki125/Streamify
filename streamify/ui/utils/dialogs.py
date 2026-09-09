# pyright: reportUnknownMemberType=none
from __future__ import annotations

from PyQt6.QtWidgets import QInputDialog, QWidget

from streamify.backend.core.models import Quality


def ask_quality_dialog(parent: QWidget, fetched_qualities: list[str]) -> Quality | None:
    """Prompts the user for stream quality, returning a Quality Enum."""

    valid_enum_values = [q.value for q in Quality]

    display_qualities = [q for q in fetched_qualities if q in valid_enum_values]

    if not display_qualities:
        display_qualities = [
            Quality.best.value,
            Quality.worst.value,
            Quality.audio_only.value,
        ]

    quality_str, ok = QInputDialog.getItem(
        parent, "Select Quality", "Available Qualities:", display_qualities, 0, False
    )

    if ok and quality_str:
        return Quality(quality_str)

    return None
