"""ARPAE Weather integration."""

from __future__ import annotations

from datetime import timedelta
import logging

import voluptuous as vol

from homeassistant.const import CONF_SCAN_INTERVAL, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.config_entries import ConfigEntry, SOURCE_IMPORT

from .api import ArpaeWeatherClient
from .const import (
    CONF_ALERT_ZONE,
    CONF_PROVINCE,
    CONF_SCAN_INTERVAL_SECONDS,
    CONF_ZONE,
    DEFAULT_ALERT_ZONE,
    DEFAULT_PROVINCE,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL_SECONDS,
    DEFAULT_ZONE,
    DOMAIN,
    VALID_PROVINCES,
    VALID_ZONES,
)
from .coordinator import ArpaeWeatherCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: tuple[Platform, ...] = (Platform.SENSOR, Platform.WEATHER)


def _uppercase(value: str) -> str:
    """Normalize YAML string values to uppercase."""
    return value.upper()


CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Optional(CONF_PROVINCE, default=DEFAULT_PROVINCE): vol.All(
                    cv.string, _uppercase, vol.In(VALID_PROVINCES)
                ),
                vol.Optional(CONF_ZONE, default=DEFAULT_ZONE): vol.All(
                    cv.string, _uppercase, vol.In(VALID_ZONES)
                ),
                vol.Optional(CONF_ALERT_ZONE, default=DEFAULT_ALERT_ZONE): vol.All(
                    cv.string, _uppercase
                ),
                vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): cv.time_period,
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up ARPAE Weather YAML imports."""
    conf = config.get(DOMAIN)
    if conf is None:
        return True

    await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_IMPORT},
        data={
            CONF_PROVINCE: conf[CONF_PROVINCE],
            CONF_ZONE: conf[CONF_ZONE],
            CONF_ALERT_ZONE: conf[CONF_ALERT_ZONE],
            CONF_SCAN_INTERVAL_SECONDS: int(conf[CONF_SCAN_INTERVAL].total_seconds()),
        },
    )
    return True


def _entry_value(entry: ConfigEntry, key: str, default: object) -> object:
    """Return an option value, falling back to entry data."""
    return entry.options.get(key, entry.data.get(key, default))


async def _async_options_updated(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload the config entry after options updates."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up ARPAE Weather from a config entry."""
    client = ArpaeWeatherClient(async_get_clientsession(hass))
    coordinator = ArpaeWeatherCoordinator(
        hass=hass,
        client=client,
        province=str(_entry_value(entry, CONF_PROVINCE, DEFAULT_PROVINCE)),
        zone=str(_entry_value(entry, CONF_ZONE, DEFAULT_ZONE)),
        alert_zone=str(_entry_value(entry, CONF_ALERT_ZONE, DEFAULT_ALERT_ZONE)),
        update_interval=timedelta(
            seconds=int(
                _entry_value(
                    entry,
                    CONF_SCAN_INTERVAL_SECONDS,
                    DEFAULT_SCAN_INTERVAL_SECONDS,
                )
            )
        ),
    )
    try:
        await coordinator.async_config_entry_first_refresh()
    except ConfigEntryNotReady:
        raise
    except Exception as err:
        raise ConfigEntryNotReady from err

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    entry.async_on_unload(entry.add_update_listener(_async_options_updated))
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload an ARPAE Weather config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
        if not hass.data[DOMAIN]:
            hass.data.pop(DOMAIN)
    return unload_ok
