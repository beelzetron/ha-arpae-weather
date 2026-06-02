"""Sensors for the ARPAE Weather integration."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Callable

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import ArpaeWeatherData, ForecastDay
from .const import (
    ATTR_COLOR,
    ATTR_DESCRIPTION,
    ATTR_ENDS_AT,
    ATTR_LINK,
    ATTR_PHENOMENA,
    ATTR_STARTS_AT,
    ATTR_TITLE,
    ATTR_VALIDITA,
    ATTR_ZONE,
    DOMAIN,
)
from .coordinator import ArpaeWeatherCoordinator


@dataclass(frozen=True, kw_only=True)
class ArpaeSensorDescription(SensorEntityDescription):
    """Description for an ARPAE sensor."""

    value_fn: Callable[[ArpaeWeatherData], str | None]
    attributes_fn: Callable[[ArpaeWeatherData], dict[str, Any]]
    icon: str


def _forecast_at(data: ArpaeWeatherData, index: int) -> ForecastDay | None:
    return data.forecasts[index] if len(data.forecasts) > index else None


def _forecast_value(index: int) -> Callable[[ArpaeWeatherData], str | None]:
    def value(data: ArpaeWeatherData) -> str | None:
        day = _forecast_at(data, index)
        if not day or not day.slots:
            return None
        return day.slots[0].condition

    return value


def _forecast_attributes(index: int) -> Callable[[ArpaeWeatherData], dict[str, Any]]:
    def attributes(data: ArpaeWeatherData) -> dict[str, Any]:
        day = _forecast_at(data, index)
        if day is None:
            return {}
        return {
            ATTR_VALIDITA: day.validita,
            "tmin": day.tmin,
            "tmax": day.tmax,
            "precipitation": day.precipitation,
            "wind": day.wind,
            "regional_sky": day.regional_sky,
            "slots": [asdict(slot) for slot in day.slots],
        }

    return attributes


def _alert_level_value(data: ArpaeWeatherData) -> str:
    return data.alert.color if data.alert else "none"


def _alert_level_attributes(data: ArpaeWeatherData) -> dict[str, Any]:
    if data.alert is None:
        return {ATTR_PHENOMENA: []}
    return {
        ATTR_ZONE: data.alert.zone,
        ATTR_COLOR: data.alert.color,
        ATTR_TITLE: data.alert.title,
        ATTR_LINK: data.alert.link,
        ATTR_STARTS_AT: data.alert.starts_at,
        ATTR_ENDS_AT: data.alert.ends_at,
        ATTR_DESCRIPTION: data.alert.description,
        ATTR_PHENOMENA: [asdict(item) for item in data.alert.phenomena],
    }


def _alert_phenomena_value(data: ArpaeWeatherData) -> str:
    if data.alert is None:
        return "none"
    return ", ".join(item.label for item in data.alert.phenomena)


def _tendency_value(data: ArpaeWeatherData) -> str:
    return "available" if data.tendency else "unavailable"


SENSOR_DESCRIPTIONS: tuple[ArpaeSensorDescription, ...] = (
    ArpaeSensorDescription(
        key="alert_level",
        name="ARPAE Weather Alert Level",
        icon="mdi:alert-outline",
        value_fn=_alert_level_value,
        attributes_fn=_alert_level_attributes,
    ),
    ArpaeSensorDescription(
        key="alert_phenomena",
        name="ARPAE Weather Alert Phenomena",
        icon="mdi:weather-lightning-rainy",
        value_fn=_alert_phenomena_value,
        attributes_fn=lambda data: _alert_level_attributes(data),
    ),
    ArpaeSensorDescription(
        key="today",
        name="ARPAE Weather Today",
        icon="mdi:weather-partly-cloudy",
        value_fn=_forecast_value(0),
        attributes_fn=_forecast_attributes(0),
    ),
    ArpaeSensorDescription(
        key="tomorrow",
        name="ARPAE Weather Tomorrow",
        icon="mdi:weather-partly-cloudy",
        value_fn=_forecast_value(1),
        attributes_fn=_forecast_attributes(1),
    ),
    ArpaeSensorDescription(
        key="day_after_tomorrow",
        name="ARPAE Weather Day After Tomorrow",
        icon="mdi:weather-partly-cloudy",
        value_fn=_forecast_value(2),
        attributes_fn=_forecast_attributes(2),
    ),
    ArpaeSensorDescription(
        key="tendency",
        name="ARPAE Weather Tendency",
        icon="mdi:chart-line",
        value_fn=_tendency_value,
        attributes_fn=lambda data: {"text": data.tendency, "emission": data.emission},
    ),
)


async def async_setup_platform(
    hass: HomeAssistant,
    config: dict[str, Any],
    async_add_entities: AddEntitiesCallback,
    discovery_info: dict[str, Any] | None = None,
) -> None:
    """Set up ARPAE Weather sensors."""
    coordinator: ArpaeWeatherCoordinator = hass.data[DOMAIN]
    async_add_entities(
        ArpaeWeatherSensor(coordinator, description)
        for description in SENSOR_DESCRIPTIONS
    )


class ArpaeWeatherSensor(CoordinatorEntity[ArpaeWeatherCoordinator], SensorEntity):
    """Representation of an ARPAE Weather sensor."""

    entity_description: ArpaeSensorDescription
    _attr_has_entity_name = False

    def __init__(
        self,
        coordinator: ArpaeWeatherCoordinator,
        description: ArpaeSensorDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{DOMAIN}_{description.key}"
        self._attr_name = description.name
        self._attr_icon = description.icon

    @property
    def native_value(self) -> str | None:
        """Return the sensor state."""
        if self.coordinator.data is None:
            return None
        return self.entity_description.value_fn(self.coordinator.data)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra sensor attributes."""
        if self.coordinator.data is None:
            return {}
        return self.entity_description.attributes_fn(self.coordinator.data)

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success and self.coordinator.data is not None
