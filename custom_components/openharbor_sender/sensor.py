from __future__ import annotations

import logging
from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event

from .const import CONF_PORT_ID, CONF_SENSOR_MAP, DOMAIN

_LOGGER = logging.getLogger(__name__)

SENSOR_NAMES: dict[str, str] = {
    "air_temperature":   "Temperatura del aire",
    "humidity":          "Humedad",
    "wind_speed":        "Velocidad del viento",
    "wind_direction":    "Dirección del viento",
    "wave_height":       "Altura de las olas",
    "water_temperature": "Temperatura del agua",
    "berths_available":  "Amarres disponibles",
    "port_status":       "Estado del puerto",
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]["sender"]
    port_data = coordinator.data or {}
    sensors = port_data.get("sensors", {})

    sensor_map = (
        entry.options.get(CONF_SENSOR_MAP)
        or entry.data.get(CONF_SENSOR_MAP, {})
    )
    async_add_entities(
        OpenHarborSenderMirrorSensor(
            hass=hass,
            entry=entry,
            port_id=entry.data[CONF_PORT_ID],
            sensor_key=key,
            source_entity_id=sensor_map[key],
            unit=meta.get("unit"),
            icon=meta.get("icon", "mdi:gauge"),
        )
        for key, meta in sensors.items()
        if not meta.get("writable", False) and key in sensor_map
    )


class OpenHarborSenderMirrorSensor(SensorEntity):
    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        port_id: str,
        sensor_key: str,
        source_entity_id: str,
        unit: str | None,
        icon: str,
    ) -> None:
        self.hass = hass
        self._entry = entry
        self._port_id = port_id
        self._sensor_key = sensor_key
        self._source_entity_id = source_entity_id
        self._attr_unique_id = f"{DOMAIN}_{port_id}_{sensor_key}"
        self._attr_name = SENSOR_NAMES.get(sensor_key, sensor_key.replace("_", " ").title())
        self._attr_native_unit_of_measurement = unit or None
        self._attr_icon = icon

    async def async_added_to_hass(self) -> None:
        @callback
        def _handle_state_change(event) -> None:
            self.async_write_ha_state()

        self.async_on_remove(
            async_track_state_change_event(
                self.hass,
                [self._source_entity_id],
                _handle_state_change,
            )
        )

    @property
    def native_value(self):
        state = self.hass.states.get(self._source_entity_id)
        if state is None or state.state in ("unknown", "unavailable", "None"):
            return None
        try:
            return float(state.state)
        except (ValueError, TypeError):
            if self._attr_native_unit_of_measurement:
                return None
            return state.state

    @property
    def extra_state_attributes(self) -> dict:
        return {
            "source_entity": self._source_entity_id,
            "sensor_key": self._sensor_key,
        }

    @property
    def device_info(self) -> dict:
        return {
            "identifiers": {(DOMAIN, self._port_id)},
            "name": f"Open Harbor Sender — {self._port_id.replace('_', ' ').title()}",
            "manufacturer": "Open Harbor",
            "model": "Sender",
        }
