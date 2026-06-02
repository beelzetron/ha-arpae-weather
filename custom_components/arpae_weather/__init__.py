"""ARPAE Weather integration."""

from __future__ import annotations

import logging

import voluptuous as vol

from homeassistant.const import CONF_SCAN_INTERVAL, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.discovery import async_load_platform

from .api import ArpaeWeatherClient
from .const import (
    CONF_ALERT_ZONE,
    CONF_PROVINCE,
    CONF_ZONE,
    DEFAULT_ALERT_ZONE,
    DEFAULT_PROVINCE,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_ZONE,
    DOMAIN,
    VALID_PROVINCES,
    VALID_ZONES,
)
from .coordinator import ArpaeWeatherCoordinator

_LOGGER = logging.getLogger(__name__)


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
    """Set up ARPAE Weather from YAML."""
    conf = config.get(DOMAIN)
    if conf is None:
        return True

    client = ArpaeWeatherClient(async_get_clientsession(hass))
    coordinator = ArpaeWeatherCoordinator(
        hass=hass,
        client=client,
        province=conf[CONF_PROVINCE],
        zone=conf[CONF_ZONE],
        alert_zone=conf[CONF_ALERT_ZONE],
        update_interval=conf[CONF_SCAN_INTERVAL],
    )
    await coordinator.async_refresh()
    if not coordinator.last_update_success:
        _LOGGER.warning("Initial ARPAE weather refresh failed; sensors will retry later")

    hass.data[DOMAIN] = coordinator
    await async_load_platform(hass, Platform.SENSOR, DOMAIN, {}, config)
    await async_load_platform(hass, Platform.WEATHER, DOMAIN, {}, config)
    return True
