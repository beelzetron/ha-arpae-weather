"""Config flow for the ARPAE Weather integration."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_SCAN_INTERVAL
from homeassistant.core import callback
from homeassistant.helpers import config_validation as cv

from .const import (
    CONF_ALERT_ZONE,
    CONF_PROVINCE,
    CONF_SCAN_INTERVAL_SECONDS,
    CONF_ZONE,
    DEFAULT_ALERT_ZONE,
    DEFAULT_PROVINCE,
    DEFAULT_SCAN_INTERVAL_SECONDS,
    DEFAULT_ZONE,
    DOMAIN,
    VALID_PROVINCES,
    VALID_ZONES,
)

CONF_SCAN_INTERVAL_MINUTES = "scan_interval_minutes"
DEFAULT_SCAN_INTERVAL_MINUTES = DEFAULT_SCAN_INTERVAL_SECONDS // 60
TITLE = "ARPAE Weather"


def _uppercase(value: str) -> str:
    """Normalize string values to uppercase."""
    return value.upper()


def _data_schema(defaults: Mapping[str, Any]) -> vol.Schema:
    """Return the config form schema."""
    scan_interval_seconds = int(
        defaults.get(CONF_SCAN_INTERVAL_SECONDS, DEFAULT_SCAN_INTERVAL_SECONDS)
    )
    return vol.Schema(
        {
            vol.Required(
                CONF_PROVINCE,
                default=defaults.get(CONF_PROVINCE, DEFAULT_PROVINCE),
            ): vol.All(cv.string, _uppercase, vol.In(VALID_PROVINCES)),
            vol.Required(
                CONF_ZONE,
                default=defaults.get(CONF_ZONE, DEFAULT_ZONE),
            ): vol.All(cv.string, _uppercase, vol.In(VALID_ZONES)),
            vol.Required(
                CONF_ALERT_ZONE,
                default=defaults.get(CONF_ALERT_ZONE, DEFAULT_ALERT_ZONE),
            ): vol.All(cv.string, _uppercase),
            vol.Required(
                CONF_SCAN_INTERVAL_MINUTES,
                default=max(1, scan_interval_seconds // 60),
            ): vol.All(vol.Coerce(int), vol.Range(min=1)),
        }
    )


def _entry_data_from_user_input(user_input: Mapping[str, Any]) -> dict[str, Any]:
    """Convert form data to config-entry data."""
    return {
        CONF_PROVINCE: str(user_input[CONF_PROVINCE]).upper(),
        CONF_ZONE: str(user_input[CONF_ZONE]).upper(),
        CONF_ALERT_ZONE: str(user_input[CONF_ALERT_ZONE]).upper(),
        CONF_SCAN_INTERVAL_SECONDS: int(user_input[CONF_SCAN_INTERVAL_MINUTES]) * 60,
    }


def _entry_data_from_import(import_data: Mapping[str, Any]) -> dict[str, Any]:
    """Convert YAML import data to config-entry data."""
    scan_interval = import_data.get(CONF_SCAN_INTERVAL)
    if scan_interval is not None:
        scan_interval_seconds = int(scan_interval.total_seconds())
    else:
        scan_interval_seconds = int(
            import_data.get(
                CONF_SCAN_INTERVAL_SECONDS,
                DEFAULT_SCAN_INTERVAL_SECONDS,
            )
        )
    return {
        CONF_PROVINCE: str(import_data.get(CONF_PROVINCE, DEFAULT_PROVINCE)).upper(),
        CONF_ZONE: str(import_data.get(CONF_ZONE, DEFAULT_ZONE)).upper(),
        CONF_ALERT_ZONE: str(
            import_data.get(CONF_ALERT_ZONE, DEFAULT_ALERT_ZONE)
        ).upper(),
        CONF_SCAN_INTERVAL_SECONDS: scan_interval_seconds,
    }


class ArpaeWeatherConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle an ARPAE Weather config flow."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> ArpaeWeatherOptionsFlow:
        """Create the options flow."""
        return ArpaeWeatherOptionsFlow(config_entry)

    async def async_step_user(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> config_entries.ConfigFlowResult:
        """Handle the initial user step."""
        if user_input is not None:
            await self.async_set_unique_id(DOMAIN)
            self._abort_if_unique_id_configured()
            return self.async_create_entry(
                title=TITLE,
                data=_entry_data_from_user_input(user_input),
            )

        return self.async_show_form(
            step_id="user",
            data_schema=_data_schema({}),
        )

    async def async_step_import(
        self,
        import_data: dict[str, Any],
    ) -> config_entries.ConfigFlowResult:
        """Import YAML configuration."""
        data = _entry_data_from_import(import_data)
        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured(updates=data)
        return self.async_create_entry(title=TITLE, data=data)


class ArpaeWeatherOptionsFlow(config_entries.OptionsFlow):
    """Handle ARPAE Weather options."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize the options flow."""
        self._config_entry = config_entry

    async def async_step_init(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> config_entries.ConfigFlowResult:
        """Manage integration options."""
        if user_input is not None:
            return self.async_create_entry(
                title="",
                data=_entry_data_from_user_input(user_input),
            )

        defaults = {**self._config_entry.data, **self._config_entry.options}
        return self.async_show_form(
            step_id="init",
            data_schema=_data_schema(defaults),
        )
