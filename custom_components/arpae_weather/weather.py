"""Weather entity for the ARPAE Weather integration."""

from __future__ import annotations

from typing import Any

from homeassistant.components.weather import WeatherEntity, WeatherEntityFeature
from homeassistant.const import UnitOfPrecipitationDepth, UnitOfSpeed, UnitOfTemperature
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import build_daily_forecast, current_condition
from .const import DOMAIN
from .coordinator import ArpaeWeatherCoordinator


async def async_setup_platform(
    hass: HomeAssistant,
    config: dict[str, Any],
    async_add_entities: AddEntitiesCallback,
    discovery_info: dict[str, Any] | None = None,
) -> None:
    """Set up the ARPAE Weather weather entity."""
    coordinator: ArpaeWeatherCoordinator = hass.data[DOMAIN]
    async_add_entities([ArpaeWeatherEntity(coordinator)])


class ArpaeWeatherEntity(CoordinatorEntity[ArpaeWeatherCoordinator], WeatherEntity):
    """Representation of ARPAE daily weather forecasts."""

    _attr_has_entity_name = False
    _attr_name = "ARPAE Weather"
    _attr_unique_id = f"{DOMAIN}_weather"
    _attr_supported_features = WeatherEntityFeature.FORECAST_DAILY
    _attr_native_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_native_precipitation_unit = UnitOfPrecipitationDepth.MILLIMETERS
    _attr_native_wind_speed_unit = UnitOfSpeed.KILOMETERS_PER_HOUR

    @property
    def condition(self) -> str | None:
        """Return the current weather condition."""
        if self.coordinator.data is None:
            return None
        return current_condition(self.coordinator.data.forecasts)

    async def async_forecast_daily(self) -> list[dict[str, object]] | None:
        """Return the daily forecast in native units."""
        if self.coordinator.data is None:
            return None
        return build_daily_forecast(self.coordinator.data.forecasts)

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success and self.coordinator.data is not None

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        super()._handle_coordinator_update()
        self.hass.async_create_task(self.async_update_listeners({"daily"}))
