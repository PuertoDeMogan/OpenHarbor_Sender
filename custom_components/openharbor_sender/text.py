from __future__ import annotations

import logging
from homeassistant.components.text import TextEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_GITHUB_TOKEN, CONF_PORT_ID, DOMAIN
from .coordinator import OpenHarborSenderCoordinator
from .github_client import GitHubClient

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: OpenHarborSenderCoordinator = hass.data[DOMAIN][entry.entry_id]["sender"]
    port_data = coordinator.data or {}

    entities = [
        OpenHarborSenderCameraUrl(entry, coordinator, cam)
        for cam in port_data.get("cameras", [])
        if cam.get("writable", False)
    ]
    async_add_entities(entities)


class OpenHarborSenderCameraUrl(CoordinatorEntity[OpenHarborSenderCoordinator], TextEntity):
    _attr_icon = "mdi:webcam"
    _attr_native_max = 500

    def __init__(self, entry: ConfigEntry, coordinator: OpenHarborSenderCoordinator, cam: dict) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._cam_id = cam["id"]
        self._attr_unique_id = f"{DOMAIN}_{entry.data[CONF_PORT_ID]}_camera_{cam['id']}_url"
        self._attr_name = f"{cam.get('name', cam['id'])} — Stream URL"
        self._attr_native_value = cam.get("stream_url", "")

    @callback
    def _handle_coordinator_update(self) -> None:
        for cam in self.coordinator.data.get("cameras", []):
            if cam["id"] == self._cam_id:
                self._attr_native_value = cam.get("stream_url", "")
                break
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

    async def async_set_value(self, value: str) -> None:
        self._attr_native_value = value
        self.async_write_ha_state()
        await self._publish(value)

    async def _publish(self, value: str) -> None:
        port_id = self._entry.data[CONF_PORT_ID]
        client = GitHubClient(self._entry.data[CONF_GITHUB_TOKEN], async_get_clientsession(self.hass))

        async with self.coordinator.write_lock:
            try:
                current = await client.get_port_data(port_id)
                for cam in current.get("cameras", []):
                    if cam["id"] == self._cam_id:
                        cam["stream_url"] = value
                        break
                await client.put_port_data(port_id, current)
                _LOGGER.debug("OpenHarborSenderCameraUrl %s → %s published", self._cam_id, value)
            except Exception as err:
                _LOGGER.error("Error publishing camera url %s: %s", self._cam_id, err)
