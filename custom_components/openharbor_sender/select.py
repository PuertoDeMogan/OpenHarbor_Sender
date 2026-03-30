from __future__ import annotations

import logging
from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import CONF_GITHUB_TOKEN, CONF_PORT_ID, DOMAIN
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
    port_data = hass.data[DOMAIN][entry.entry_id].get("last_port_data", {})
    sensors = port_data.get("sensors", {})

    entities = [
        OpenHarborSenderSelect(hass, entry, key, meta)
        for key, meta in sensors.items()
        if meta.get("writable") and meta.get("type") == "select"
    ]
    async_add_entities(entities)


class OpenHarborSenderSelect(SelectEntity):
    def __init__(self, hass, entry, sensor_key, meta):
        self.hass = hass
        self._entry = entry
        self._sensor_key = sensor_key
        self._meta = meta
        self._attr_unique_id = f"{DOMAIN}_{entry.data[CONF_PORT_ID]}_{sensor_key}"        
        self._attr_name = SENSOR_NAMES.get(sensor_key, sensor_key.replace("_", " ").title())
        self._attr_icon = meta.get("icon", "mdi:form-select")
        self._attr_options = meta.get("options", [])
        self._attr_current_option = str(meta.get("value", self._attr_options[0] if self._attr_options else ""))

    @property
    def device_info(self):
        port_data = self.hass.data[DOMAIN][self._entry.entry_id].get("last_port_data", {})
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
        entry = self._entry
        port_id = entry.data[CONF_PORT_ID]
        client = GitHubClient(entry.data[CONF_GITHUB_TOKEN], async_get_clientsession(self.hass))

        try:
            current = await client.get_port_data(port_id)
            if self._sensor_key in current.get("sensors", {}):
                current["sensors"][self._sensor_key]["value"] = value
            await client.put_port_data(port_id, current)
            self.hass.data[DOMAIN][entry.entry_id]["last_port_data"] = current
            _LOGGER.debug("OpenHarborSenderSelect %s → %s published", self._sensor_key, value)
        except Exception as err:
            _LOGGER.error("Error publishing %s: %s", self._sensor_key, err)
