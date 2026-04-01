from __future__ import annotations

import logging
from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_GITHUB_TOKEN, CONF_PORT_ID, DOMAIN
from .coordinator import OpenHarborSenderCoordinator
from .github_client import GitHubClient

_LOGGER = logging.getLogger(__name__)

SENSOR_NAMES: dict[str, str] = {
    "port_status":       "Estado del puerto",
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: OpenHarborSenderCoordinator = hass.data[DOMAIN][entry.entry_id]["sender"]
    sensors = coordinator.data.get("sensors", {}) if coordinator.data else {}

    entities = [
        OpenHarborSenderSelect(entry, coordinator, key, meta)
        for key, meta in sensors.items()
        if meta.get("writable") and meta.get("type") == "select"
    ]
    async_add_entities(entities)


class OpenHarborSenderSelect(CoordinatorEntity[OpenHarborSenderCoordinator], SelectEntity):
    def __init__(self, entry: ConfigEntry, coordinator: OpenHarborSenderCoordinator, sensor_key: str, meta: dict):
        super().__init__(coordinator)
        self._entry = entry
        self._sensor_key = sensor_key
        self._attr_unique_id = f"{DOMAIN}_{entry.data[CONF_PORT_ID]}_{sensor_key}"
        self._attr_name = SENSOR_NAMES.get(sensor_key, sensor_key.replace("_", " ").title())
        self._attr_icon = meta.get("icon", "mdi:form-select")
        self._attr_options = meta.get("options", [])
        self._attr_current_option = str(meta.get("value", self._attr_options[0] if self._attr_options else ""))

    @callback
    def _handle_coordinator_update(self) -> None:
        sensor = self.coordinator.data.get("sensors", {}).get(self._sensor_key, {})
        val = sensor.get("value")
        if val is not None:
            self._attr_current_option = str(val)
        options = sensor.get("options")
        if options:
            self._attr_options = options
        self.async_write_ha_state()

    @property
    def device_info(self):
        port_data = self.coordinator.data or {}
        return {
            "identifiers": {(DOMAIN, self._entry.data[CONF_PORT_ID])},
            "name": port_data.get("name", self._entry.data[CONF_PORT_ID]),
            "manufacturer": "Open Harbor",
            "model": "Sender",
        }

    async def async_select_option(self, option: str) -> None:
        self._attr_current_option = option
        self.async_write_ha_state()
        await self._publish(option)

    async def _publish(self, value) -> None:
        port_id = self._entry.data[CONF_PORT_ID]
        client = GitHubClient(self._entry.data[CONF_GITHUB_TOKEN], async_get_clientsession(self.hass))

        async with self.coordinator.write_lock:
            try:
                current = await client.get_port_data(port_id)
                if self._sensor_key in current.get("sensors", {}):
                    current["sensors"][self._sensor_key]["value"] = value
                await client.put_port_data(port_id, current)
                _LOGGER.debug("OpenHarborSenderSelect %s → %s published", self._sensor_key, value)
            except Exception as err:
                _LOGGER.error("Error publishing %s: %s", self._sensor_key, err)
