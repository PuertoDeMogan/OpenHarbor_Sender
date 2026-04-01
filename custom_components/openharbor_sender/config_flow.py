from __future__ import annotations

import asyncio
import logging

import aiohttp
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers import selector
from homeassistant.helpers.selector import (
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
)

from .const import (
    CONF_GITHUB_TOKEN,
    CONF_PORT_ID,
    CONF_SENSOR_MAP,
    CONF_UPDATE_INTERVAL,
    DATA_API_BASE,
    DEFAULT_UPDATE_INTERVAL,
    MIN_UPDATE_INTERVAL,
    MAX_UPDATE_INTERVAL,
    DOMAIN,
)
from .github_client import GitHubClient

_LOGGER = logging.getLogger(__name__)


async def _fetch_available_ports(session: aiohttp.ClientSession) -> dict[str, str]:
    headers = {"Accept": "application/vnd.github+json"}

    async with session.get(
        DATA_API_BASE,
        headers=headers,
        timeout=aiohttp.ClientTimeout(total=10),
    ) as resp:
        resp.raise_for_status()
        files: list[dict] = await resp.json(content_type=None)

    port_files = [
        f for f in files
        if f.get("type") == "file" and f["name"].endswith(".json")
    ]

    async def _fetch_port_name(file_entry: dict) -> tuple[str, str]:
        port_id = file_entry["name"].removesuffix(".json")
        try:
            async with session.get(
                file_entry["download_url"],
                timeout=aiohttp.ClientTimeout(total=10),
            ) as r:
                r.raise_for_status()
                data = await r.json(content_type=None)
                name = data.get("name", port_id.replace("_", " ").title())
        except Exception:
            _LOGGER.warning("Could not fetch name for port %s, using fallback", port_id)
            name = port_id.replace("_", " ").title()
        return port_id, name

    results = await asyncio.gather(*[_fetch_port_name(f) for f in port_files])
    return dict(results)


class OpenHarborSenderConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self) -> None:
        self._port_id: str = ""
        self._token: str = ""
        self._port_data: dict = {}
        self._sensor_map: dict = {}
        self._available_ports: dict[str, str] = {}

    async def async_step_user(
        self, user_input: dict | None = None
    ) -> FlowResult:
        errors: dict[str, str] = {}

        if not self._available_ports:
            try:
                session = async_get_clientsession(self.hass)
                self._available_ports = await _fetch_available_ports(session)
            except aiohttp.ClientResponseError:
                errors["base"] = "cannot_connect"
            except aiohttp.ClientError:
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected error fetching port list")
                errors["base"] = "unknown"

        if not errors and user_input is not None:
            self._port_id = user_input[CONF_PORT_ID]
            self._token = user_input[CONF_GITHUB_TOKEN].strip()

            await self.async_set_unique_id(f"{DOMAIN}_{self._port_id}")
            self._abort_if_unique_id_configured()

            client = GitHubClient(self._token, async_get_clientsession(self.hass))
            try:
                await client.validate_token()
                self._port_data = await client.get_port_data(self._port_id)
            except ValueError as err:
                errors["base"] = str(err)
            except Exception:
                errors["base"] = "cannot_connect"
            else:
                return await self.async_step_sensor_map()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_GITHUB_TOKEN): cv.string,
                    vol.Required(CONF_PORT_ID): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=[
                                {"value": pid, "label": name}
                                for pid, name in self._available_ports.items()
                            ],
                            mode=selector.SelectSelectorMode.DROPDOWN,
                        )
                    ),
                }
            ),
            errors=errors,
        )

    async def async_step_sensor_map(
        self, user_input: dict | None = None
    ) -> FlowResult:
        if user_input is not None:
            self._sensor_map = user_input
            return await self.async_step_cadence()

        sensors = self._port_data.get("sensors", {})

        readonly_sensors = {
            key: meta
            for key, meta in sensors.items()
            if not meta.get("writable", False)
        }

        schema_dict = {}
        for sensor_key in readonly_sensors:
            schema_dict[vol.Required(sensor_key)] = selector.selector(
                {"entity": {}}
            )

        return self.async_show_form(
            step_id="sensor_map",
            data_schema=vol.Schema(schema_dict),
            description_placeholders={
                "port_name": self._port_data.get("name", self._port_id)
            },
        )

    async def async_step_cadence(
        self, user_input: dict | None = None
    ) -> FlowResult:
        if user_input is not None:
            return self.async_create_entry(
                title=self._port_data.get("name", self._port_id),
                data={
                    CONF_PORT_ID: self._port_id,
                    CONF_GITHUB_TOKEN: self._token,
                    CONF_SENSOR_MAP: self._sensor_map,
                    CONF_UPDATE_INTERVAL: int(user_input[CONF_UPDATE_INTERVAL]),
                },
            )

        return self.async_show_form(
            step_id="cadence",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_UPDATE_INTERVAL, default=DEFAULT_UPDATE_INTERVAL
                    ): NumberSelector(
                        NumberSelectorConfig(
                            min=MIN_UPDATE_INTERVAL,
                            max=MAX_UPDATE_INTERVAL,
                            step=1,
                            mode=NumberSelectorMode.BOX,
                            unit_of_measurement="min",
                        )
                    )
                }
            ),
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry):
        return OpenHarborSenderOptionsFlow(config_entry)


class OpenHarborSenderOptionsFlow(config_entries.OptionsFlow):
    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self._config_entry = config_entry
        self._new_sensor_map: dict = {}

    async def async_step_init(
        self, user_input: dict | None = None
    ) -> FlowResult:
        if user_input is not None:
            self._new_sensor_map = user_input
            return await self.async_step_cadence()

        client = GitHubClient(
            self._config_entry.data[CONF_GITHUB_TOKEN],
            async_get_clientsession(self.hass),
        )
        try:
            port_data = await client.get_port_data(self._config_entry.data[CONF_PORT_ID])
        except Exception:
            port_data = {}

        sensors = port_data.get("sensors", {})
        current_map = self._config_entry.data.get(CONF_SENSOR_MAP, {})

        schema_dict = {}
        for sensor_key, meta in sensors.items():
            if meta.get("writable", False):
                continue
            schema_dict[vol.Required(
                sensor_key,
                default=current_map.get(sensor_key)
            )] = selector.selector({"entity": {}})

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(schema_dict),
            description_placeholders={
                "port_name": port_data.get("name", self._config_entry.data[CONF_PORT_ID])
            },
        )

    async def async_step_cadence(
        self, user_input: dict | None = None
    ) -> FlowResult:
        if user_input is not None:
            return self.async_create_entry(
                title="",
                data={
                    CONF_UPDATE_INTERVAL: int(user_input[CONF_UPDATE_INTERVAL]),
                    CONF_SENSOR_MAP: self._new_sensor_map,
                },
            )

        current = self._config_entry.options or {}
        data = self._config_entry.data

        return self.async_show_form(
            step_id="cadence",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_UPDATE_INTERVAL,
                        default=current.get(
                            CONF_UPDATE_INTERVAL,
                            data.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL),
                        ),
                    ): NumberSelector(
                        NumberSelectorConfig(
                            min=MIN_UPDATE_INTERVAL,
                            max=MAX_UPDATE_INTERVAL,
                            step=1,
                            mode=NumberSelectorMode.BOX,
                            unit_of_measurement="min",
                        )
                    )
                }
            ),
        )
