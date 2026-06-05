"""Tests for the ARPAE Weather config flow."""

from __future__ import annotations

from datetime import timedelta

from homeassistant import config_entries
from homeassistant.const import CONF_SCAN_INTERVAL
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.arpae_weather.config_flow import CONF_SCAN_INTERVAL_MINUTES
from custom_components.arpae_weather.const import (
    CONF_ALERT_ZONE,
    CONF_PROVINCE,
    CONF_SCAN_INTERVAL_SECONDS,
    CONF_ZONE,
    DEFAULT_ALERT_ZONE,
    DEFAULT_PROVINCE,
    DEFAULT_SCAN_INTERVAL_SECONDS,
    DEFAULT_ZONE,
    DOMAIN,
)


async def test_user_flow_creates_entry(hass):
    """Test creating an entry from the user flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER},
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_PROVINCE: "mo",
            CONF_ZONE: "c",
            CONF_ALERT_ZONE: "c2",
            CONF_SCAN_INTERVAL_MINUTES: 90,
        },
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "ARPAE Weather"
    assert result["data"] == {
        CONF_PROVINCE: "MO",
        CONF_ZONE: "C",
        CONF_ALERT_ZONE: "C2",
        CONF_SCAN_INTERVAL_SECONDS: 5400,
    }


async def test_user_flow_aborts_when_already_configured(hass):
    """Test duplicate user flow handling."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=DOMAIN,
        data={
            CONF_PROVINCE: DEFAULT_PROVINCE,
            CONF_ZONE: DEFAULT_ZONE,
            CONF_ALERT_ZONE: DEFAULT_ALERT_ZONE,
            CONF_SCAN_INTERVAL_SECONDS: DEFAULT_SCAN_INTERVAL_SECONDS,
        },
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER},
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_PROVINCE: "BO",
            CONF_ZONE: "P",
            CONF_ALERT_ZONE: "C2",
            CONF_SCAN_INTERVAL_MINUTES: 120,
        },
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"


async def test_yaml_import_creates_entry(hass):
    """Test importing YAML configuration."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_IMPORT},
        data={
            CONF_PROVINCE: "mo",
            CONF_ZONE: "r",
            CONF_ALERT_ZONE: "c3",
            CONF_SCAN_INTERVAL: timedelta(hours=3),
        },
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == {
        CONF_PROVINCE: "MO",
        CONF_ZONE: "R",
        CONF_ALERT_ZONE: "C3",
        CONF_SCAN_INTERVAL_SECONDS: 10800,
    }


async def test_options_flow_updates_entry_options(hass):
    """Test updating entry options."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=DOMAIN,
        data={
            CONF_PROVINCE: "BO",
            CONF_ZONE: "P",
            CONF_ALERT_ZONE: "C2",
            CONF_SCAN_INTERVAL_SECONDS: 7200,
        },
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(entry.entry_id)

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "init"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {
            CONF_PROVINCE: "fc",
            CONF_ZONE: "r",
            CONF_ALERT_ZONE: "h2",
            CONF_SCAN_INTERVAL_MINUTES: 45,
        },
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == {
        CONF_PROVINCE: "FC",
        CONF_ZONE: "R",
        CONF_ALERT_ZONE: "H2",
        CONF_SCAN_INTERVAL_SECONDS: 2700,
    }
