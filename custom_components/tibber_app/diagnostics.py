"""Diagnostics for the Tibber app integration."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.core import HomeAssistant

from . import TibberConfigEntry
from .const import CONF_EMAIL, CONF_PASSWORD, CONF_TOKEN

# Redact credentials from the entry, and device ids / location-ish bits from data.
_REDACT = {CONF_EMAIL, CONF_PASSWORD, CONF_TOKEN, "id", "homeId", "deviceId", "title"}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: TibberConfigEntry
) -> dict[str, Any]:
    """Return redacted diagnostics for a config entry."""
    coordinator = entry.runtime_data.coordinator
    data = coordinator.data
    return {
        "entry_data": async_redact_data(dict(entry.data), _REDACT),
        "homes": len(coordinator.home_titles),
        "devices": [{"type": d.type, "name": d.name} for d in coordinator.devices],
        "grid_reward_homes": len(coordinator.grid_reward_homes),
        "last_update_success": coordinator.last_update_success,
        "seconds_since_last_seen": coordinator.stale_ages(),
        "data": async_redact_data(asdict(data) if data else {}, _REDACT),
    }
