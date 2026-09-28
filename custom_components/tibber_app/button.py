"""Button platform for the Tibber app integration."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import TibberConfigEntry
from .const import GIZMO_ELECTRIC_VEHICLE, VEHICLE_DEPARTURE_SUFFIX, WEEKDAYS
from .coordinator import TibberDataUpdateCoordinator, TibberDevice
from .entity import TibberEntity, TibberHomeEntity
from .vehicle_settings import parse_departure_time

PARALLEL_UPDATES = 0


async def async_setup_entry(
    hass: HomeAssistant,
    entry: TibberConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up refresh and vehicle schedule buttons."""
    coordinator = entry.runtime_data.coordinator
    entities: list[ButtonEntity] = [
        TibberRefreshButton(coordinator, home_id)
        for home_id in coordinator.home_titles
    ]
    for dev in coordinator.devices_of_type(GIZMO_ELECTRIC_VEHICLE):
        monday_key = coordinator.vehicle_setting_key(
            dev.id, VEHICLE_DEPARTURE_SUFFIX.format(day="monday")
        )
        if monday_key is not None:
            entities.append(TibberClearAllDepartureTimesButton(coordinator, dev))
    async_add_entities(entities)


class TibberRefreshButton(TibberHomeEntity, ButtonEntity):
    """Force an immediate data refresh."""

    _attr_translation_key = "refresh"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator: TibberDataUpdateCoordinator, home_id: str) -> None:
        super().__init__(coordinator, home_id, "refresh")

    async def async_press(self) -> None:
        await self.coordinator.async_request_refresh()


class TibberClearAllDepartureTimesButton(TibberEntity, ButtonEntity):
    """Clear every weekday that currently has a departure time."""

    _attr_translation_key = "clear_all_departure_times"
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(
        self, coordinator: TibberDataUpdateCoordinator, device: TibberDevice
    ) -> None:
        super().__init__(coordinator, device, "clear_all_departure_times")

    async def async_press(self) -> None:
        node = self.coordinator.data.vehicles.get(self._device.id) or {}
        current_settings = {
            setting.get("key"): setting.get("value")
            for setting in node.get("userSettings") or []
        }
        setting_keys = []
        for day in WEEKDAYS:
            suffix = VEHICLE_DEPARTURE_SUFFIX.format(day=day)
            key = self.coordinator.vehicle_setting_key(self._device.id, suffix)
            if (
                key is not None
                and parse_departure_time(current_settings.get(key)) is not None
            ):
                setting_keys.append(key)

        await self.coordinator.async_clear_vehicle_departure_times(
            self._device.id, self._device.home_id, setting_keys
        )
