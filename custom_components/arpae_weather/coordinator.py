"""Data coordinator for the ARPAE Weather integration."""

from __future__ import annotations

from datetime import timedelta
import logging

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import ArpaeWeatherClient, ArpaeWeatherData
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class ArpaeWeatherCoordinator(DataUpdateCoordinator[ArpaeWeatherData]):
    """Coordinate ARPAE API polling for all sensors."""

    def __init__(
        self,
        hass: HomeAssistant,
        client: ArpaeWeatherClient,
        province: str,
        zone: str,
        alert_zone: str,
        update_interval: timedelta,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=update_interval,
        )
        self._client = client
        self.province = province
        self.zone = zone
        self.alert_zone = alert_zone

    async def _async_update_data(self) -> ArpaeWeatherData:
        try:
            return await self._client.async_fetch_data(
                self.province,
                self.zone,
                self.alert_zone,
            )
        except Exception as err:
            raise UpdateFailed(f"Error fetching ARPAE weather data: {err}") from err
