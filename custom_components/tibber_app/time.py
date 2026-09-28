"""Time platform: the weekly EV smart-charging departure schedule.

Each vehicle exposes one time entity per weekday, backed by its
``…departureTimes.<day>`` user setting ("HH:MM"). Together they form the weekly
smart-charging schedule shown in the Tibber app. The setting is namespaced by how
the vehicle was added, so the full key is resolved per vehicle.
"""

from __future__ import annotations

from datetime import time as dt_time

from homeassistant.components.time import TimeEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_platform
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import TibberConfigEntry
from .const import GIZMO_ELECTRIC_VEHICLE, VEHICLE_DEPARTURE_SUFFIX, WEEKDAYS
from .coordinator import TibberDataUpdateCoordinator, TibberDevice
from .entity import TibberEntity
from .vehicle_settings import parse_departure_time

PARALLEL_UPDATES = 0


async def async_setup_entry(
    hass: HomeAssistant,
    entry: TibberConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Create a departure-time entity per weekday for each vehicle."""
    platform = entity_platform.async_get_current_platform()
    platform.async_register_entity_service(
        "clear_departure_times", {}, "async_clear_departure_time"
    )

    coordinator = entry.runtime_data.coordinator
    entities: list[TimeEntity] = []
    for dev in coordinator.devices_of_type(GIZMO_ELECTRIC_VEHICLE):
        # Only expose the schedule for vehicles that actually have it. Monday's
        # key also pins down the namespace the whole week lives in.
        monday_key = coordinator.vehicle_setting_key(
            dev.id, VEHICLE_DEPARTURE_SUFFIX.format(day="monday")
        )
        if monday_key is None:
            continue
        prefix = monday_key[: -len("monday")]
        entities += [
            TibberDepartureTime(coordinator, dev, day, prefix + day) for day in WEEKDAYS
        ]
    async_add_entities(entities)


class TibberDepartureTime(TibberEntity, TimeEntity):
    """Smart-charging departure time for one weekday."""

    def __init__(
        self,
        coordinator: TibberDataUpdateCoordinator,
        device: TibberDevice,
        weekday: str,
        setting_key: str,
    ) -> None:
        super().__init__(coordinator, device, f"departure_{weekday}")
        self._weekday = weekday
        self._suffix = VEHICLE_DEPARTURE_SUFFIX.format(day=weekday)
        self._fallback_key = setting_key
        self._attr_translation_key = f"departure_{weekday}"

    @property
    def _setting_key(self) -> str:
        """The key this vehicle currently exposes, else the one found at setup."""
        return (
            self.coordinator.vehicle_setting_key(self._device.id, self._suffix)
            or self._fallback_key
        )

    @property
    def native_value(self) -> dt_time | None:
        node = self.coordinator.data.vehicles.get(self._device.id) or {}
        key = self._setting_key
        for setting in node.get("userSettings") or []:
            if setting.get("key") == key:
                return parse_departure_time(setting.get("value"))
        return None

    async def async_set_value(self, value: dt_time) -> None:
        await self.coordinator.async_set_vehicle_setting(
            self._device.id,
            self._device.home_id,
            self._setting_key,
            value.strftime("%H:%M"),
        )

    async def async_clear_departure_time(self) -> None:
        """Clear this departure time through the standard entity action API."""
        if self.native_value is None:
            return
        await self.coordinator.async_clear_vehicle_departure_times(
            self._device.id, self._device.home_id, [self._setting_key]
        )
