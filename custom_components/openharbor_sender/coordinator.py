from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone, timedelta

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    CONF_GITHUB_TOKEN,
    CONF_PORT_ID,
    CONF_SENSOR_MAP,
    CONF_UPDATE_INTERVAL,
    DEFAULT_UPDATE_INTERVAL,
    DOMAIN,
)
from .github_client import GitHubClient

_LOGGER = logging.getLogger(__name__)


class OpenHarborSenderCoordinator(DataUpdateCoordinator):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self._entry = entry
        self._client = GitHubClient(
            entry.data[CONF_GITHUB_TOKEN],
            async_get_clientsession(hass),
        )

        interval_minutes = int(
            entry.options.get(
                CONF_UPDATE_INTERVAL,
                entry.data.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL),
            )
        )

        self.write_lock = asyncio.Lock()

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=interval_minutes),
        )

    async def _async_update_data(self) -> dict:
        port_id = self._entry.data[CONF_PORT_ID]
        sensor_map: dict = (
            self._entry.options.get(CONF_SENSOR_MAP)
            or self._entry.data.get(CONF_SENSOR_MAP, {})
        )

        async with self.write_lock:
            try:
                current = await self._client.get_port_data(port_id)
            except Exception as err:
                raise UpdateFailed(f"Cannot fetch port data for {port_id}: {err}") from err

            sensors_payload = current.get("sensors", {})
            changed = False

            for sensor_key, entity_id in sensor_map.items():
                if sensor_key not in sensors_payload:
                    continue
                state = self.hass.states.get(entity_id)
                if state is None or state.state in ("unknown", "unavailable"):
                    continue
                new_value = _parse_state(state.state)
                if sensors_payload[sensor_key].get("value") != new_value:
                    sensors_payload[sensor_key]["value"] = new_value
                    changed = True

            if not changed:
                _LOGGER.debug("openharbor_sender: %s no changes, skipping PUT", port_id)
                return current

            payload = {
                "port_id": port_id,
                "name": current.get("name", port_id),
                "last_updated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "cameras": current.get("cameras", []),
                "sensors": sensors_payload,
            }

            await self._client.put_port_data(port_id, payload)
            _LOGGER.debug("openharbor_sender: %s updated on GitHub", port_id)
            return payload


def _parse_state(value: str) -> float | str:
    try:
        return float(value)
    except (ValueError, TypeError):
        return value
