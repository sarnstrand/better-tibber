"""Helpers for Tibber vehicle settings."""

from __future__ import annotations

from datetime import time as dt_time


def parse_departure_time(value: object) -> dt_time | None:
    """Parse a valid Tibber HH:MM departure setting."""
    if not isinstance(value, str):
        return None
    parts = value.split(":")
    if len(parts) != 2 or not all(part.isdigit() for part in parts):
        return None
    hour, minute = (int(part) for part in parts)
    if not 0 <= hour <= 23 or not 0 <= minute <= 59:
        return None
    return dt_time(hour, minute)
