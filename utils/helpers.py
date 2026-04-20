"""
helpers.py — Shared utility functions for Exploding Kittens.
"""

import datetime
import textwrap
from typing import Any


def format_duration(seconds: int) -> str:
    """Convert a raw second count into a human-readable string."""
    if seconds < 60:
        return f"{seconds}s"
    minutes, secs = divmod(seconds, 60)
    if minutes < 60:
        return f"{minutes}m {secs}s"
    hours, mins = divmod(minutes, 60)
    return f"{hours}h {mins}m"


def wrap_text(text: str, width: int = 18) -> str:
    """Wrap a string to the given column width (for card labels)."""
    return "\n".join(textwrap.wrap(text, width))


def timestamp_now() -> str:
    """Return the current local time as a formatted string."""
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def clamp(value: int, lo: int, hi: int) -> int:
    """Return value clamped to [lo, hi]."""
    return max(lo, min(hi, value))


def pluralise(count: int, singular: str, plural: str | None = None) -> str:
    """Return the correctly pluralised noun phrase."""
    noun = singular if count == 1 else (plural or singular + "s")
    return f"{count} {noun}"


def validate_player_names(names: list[str]) -> tuple[bool, str]:
    """
    Validate a list of player names.

    Returns (True, "") on success, or (False, error_message) on failure.
    """
    if len(names) < 2:
        return False, "At least 2 players are required."
    if len(names) > 5:
        return False, "Maximum 5 players are allowed."
    for name in names:
        if not name.strip():
            return False, "Player names cannot be empty."
        if len(name.strip()) > 20:
            return False, f"Name '{name}' is too long (max 20 characters)."
    if len({n.lower() for n in names}) != len(names):
        return False, "All player names must be unique."
    return True, ""


def safe_int(value: Any, default: int = 0) -> int:
    """Convert value to int safely, returning default on failure."""
    try:
        return int(value)
    except (TypeError, ValueError):
        return default
