"""Tests for ARPAE Weather config-entry setup."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.exceptions import ConfigEntryNotReady
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.arpae_weather import async_setup_entry, async_unload_entry
from custom_components.arpae_weather.const import (
    CONF_ALERT_ZONE,
    CONF_PROVINCE,
    CONF_SCAN_INTERVAL_SECONDS,
    CONF_ZONE,
    DOMAIN,
)


def _mock_entry(**overrides):
    data = {
        CONF_PROVINCE: "MO",
        CONF_ZONE: "C",
        CONF_ALERT_ZONE: "C2",
        CONF_SCAN_INTERVAL_SECONDS: 5400,
    }
    data.update(overrides)
    return MockConfigEntry(domain=DOMAIN, unique_id=DOMAIN, data=data)


async def test_async_setup_entry_stores_coordinator_and_forwards_platforms(hass):
    """Test config-entry setup."""
    entry = _mock_entry()
    entry.add_to_hass(hass)

    with (
        patch(
            "custom_components.arpae_weather.ArpaeWeatherCoordinator.async_config_entry_first_refresh",
            AsyncMock(),
        ),
        patch.object(
            hass.config_entries,
            "async_forward_entry_setups",
            AsyncMock(return_value=True),
        ) as forward_entry_setups,
    ):
        assert await async_setup_entry(hass, entry) is True

    coordinator = hass.data[DOMAIN][entry.entry_id]
    assert coordinator.province == "MO"
    assert coordinator.zone == "C"
    assert coordinator.alert_zone == "C2"
    assert coordinator.update_interval.total_seconds() == 5400
    forward_entry_setups.assert_awaited_once()


async def test_async_setup_entry_uses_options_over_data(hass):
    """Test options override stored config-entry data."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=DOMAIN,
        data={
            CONF_PROVINCE: "MO",
            CONF_ZONE: "C",
            CONF_ALERT_ZONE: "C2",
            CONF_SCAN_INTERVAL_SECONDS: 5400,
        },
        options={
            CONF_PROVINCE: "FC",
            CONF_ZONE: "R",
            CONF_ALERT_ZONE: "H2",
            CONF_SCAN_INTERVAL_SECONDS: 2700,
        },
    )
    entry.add_to_hass(hass)

    with (
        patch(
            "custom_components.arpae_weather.ArpaeWeatherCoordinator.async_config_entry_first_refresh",
            AsyncMock(),
        ),
        patch.object(
            hass.config_entries,
            "async_forward_entry_setups",
            AsyncMock(return_value=True),
        ),
    ):
        assert await async_setup_entry(hass, entry) is True

    coordinator = hass.data[DOMAIN][entry.entry_id]
    assert coordinator.province == "FC"
    assert coordinator.zone == "R"
    assert coordinator.alert_zone == "H2"
    assert coordinator.update_interval.total_seconds() == 2700


async def test_async_setup_entry_raises_config_entry_not_ready(hass):
    """Test setup retry when the initial refresh fails."""
    entry = _mock_entry()
    entry.add_to_hass(hass)

    with patch(
        "custom_components.arpae_weather.ArpaeWeatherCoordinator.async_config_entry_first_refresh",
        AsyncMock(side_effect=ConfigEntryNotReady),
    ):
        with pytest.raises(ConfigEntryNotReady):
            await async_setup_entry(hass, entry)

    assert DOMAIN not in hass.data


async def test_async_unload_entry_unloads_platforms_and_removes_data(hass):
    """Test config-entry unload."""
    entry = _mock_entry()
    entry.add_to_hass(hass)
    hass.data[DOMAIN] = {entry.entry_id: object()}

    with patch.object(
        hass.config_entries,
        "async_unload_platforms",
        AsyncMock(return_value=True),
    ) as unload_platforms:
        assert await async_unload_entry(hass, entry) is True

    unload_platforms.assert_awaited_once()
    assert DOMAIN not in hass.data
