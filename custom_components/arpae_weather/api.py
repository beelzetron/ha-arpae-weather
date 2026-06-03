"""ARPAE API client and parsers."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import date, datetime, time, timezone, timedelta
from json import JSONDecodeError
import re
from typing import TYPE_CHECKING, Any

from aiohttp import ClientError, ClientResponseError

if TYPE_CHECKING:
    from aiohttp import ClientSession

FORECAST_URL = "https://apps.arpae.it/REST/meteo_bollettini/?sort=-_id&max_results=1"
ALERT_URL = "https://allertameteo.regione.emilia-romagna.it/o/get-stato-allerta"
ALERT_BASE_URL = "https://allertameteo.regione.emilia-romagna.it"
FETCH_RETRY_DELAYS = (5.0, 20.0)
RETRY_HTTP_STATUSES = {408, 429, 500, 502, 503, 504}

ALERT_SEVERITY = {
    "green": 0,
    "yellow": 1,
    "orange": 2,
    "red": 3,
}

ALERT_LABELS = {
    "idraulica": "Piene dei fiumi",
    "idrogeologica": "Frane e piene dei corsi minori",
    "temporali": "Temporali",
    "vento": "Vento",
    "neve": "Neve",
    "ghiaccio_pioggia_gela": "Ghiaccio e pioggia che gela",
    "temperature_estreme": "Temperature estreme",
    "stato_mare": "Stato del mare",
    "mareggiate": "Mareggiate",
}

SLOT_HOURS = {
    "Mattina": 12,
    "Pomeriggio": 18,
}

_NUMBER_RE = re.compile(r"[-+]?\d+(?:[,.]\d+)?")

ICON_MAP = {
    "a001": "sunny",
    "b001": "clear-night",
    "a002": "partlycloudy",
    "b002": "partlycloudy",
    "a003": "partlycloudy",
    "b003": "clear-night",
    "a004": "partlycloudy",
    "a005": "cloudy",
    "b005": "cloudy",
    "a006": "rainy",
    "b006": "rainy",
    "a007": "lightning-rainy",
    "b007": "lightning-rainy",
    "a010": "cloudy",
    "b010": "cloudy",
    "a013": "cloudy",
    "a014": "rainy",
    "a016": "rainy",
    "a017": "rainy",
    "a019": "lightning-rainy",
    "a023": "rainy",
    "a036": "rainy",
}


@dataclass(frozen=True)
class ForecastSlot:
    """One forecast period inside an ARPAE forecast day."""

    name: str
    condition: str
    icon: str


@dataclass(frozen=True)
class ForecastDay:
    """Parsed forecast data for one day."""

    label: str
    validita: str
    slots: tuple[ForecastSlot, ...]
    tmin: str | None = None
    tmax: str | None = None
    precipitation: str | None = None
    wind: str | None = None
    regional_sky: str | None = None


@dataclass(frozen=True)
class AlertPhenomenon:
    """One active weather alert phenomenon."""

    key: str
    label: str
    color: str


@dataclass(frozen=True)
class WeatherAlert:
    """Parsed active weather alert for a zone."""

    zone: str
    color: str
    title: str
    link: str | None
    starts_at: str | None
    ends_at: str | None
    description: str | None
    phenomena: tuple[AlertPhenomenon, ...]


@dataclass(frozen=True)
class ArpaeWeatherData:
    """Complete coordinator payload."""

    forecasts: tuple[ForecastDay, ...]
    alert: WeatherAlert | None
    tendency: str | None
    emission: str | None


class ArpaeWeatherError(RuntimeError):
    """Raised when ARPAE data cannot be fetched or parsed."""


def build_daily_forecast(
    forecasts: tuple[ForecastDay, ...],
    base_date: date | None = None,
) -> list[dict[str, object]]:
    """Build Home Assistant daily forecast dictionaries from parsed ARPAE days."""
    start_date = base_date or date.today()
    items: list[dict[str, object]] = []
    for offset, day in enumerate(forecasts):
        forecast: dict[str, object] = {
            "datetime": datetime.combine(
                start_date + timedelta(days=offset),
                time.min,
                tzinfo=timezone.utc,
            ).isoformat(),
        }
        if condition := forecast_condition(day):
            forecast["condition"] = condition
        if (temperature := parse_forecast_number(day.tmax)) is not None:
            forecast["native_temperature"] = temperature
        if (templow := parse_forecast_number(day.tmin)) is not None:
            forecast["native_templow"] = templow
        if (precipitation := parse_forecast_number(day.precipitation)) is not None:
            forecast["native_precipitation"] = precipitation
        if (wind_speed := parse_forecast_number(day.wind)) is not None:
            forecast["native_wind_speed"] = wind_speed
        items.append(forecast)
    return items


def forecast_condition(day: ForecastDay) -> str | None:
    """Return the best HA weather condition for an ARPAE forecast day."""
    if not day.slots:
        return None
    return day.slots[0].icon


def current_condition(
    forecasts: tuple[ForecastDay, ...],
    now: datetime | None = None,
) -> str | None:
    """Return a current condition synthesized from today's ARPAE slots."""
    if not forecasts:
        return None
    today = forecasts[0]
    if not today.slots:
        return None

    current_hour = (now or datetime.now()).hour
    for slot in today.slots:
        if current_hour < SLOT_HOURS.get(slot.name, 24):
            return slot.icon
    return today.slots[-1].icon


def parse_forecast_number(value: str | None) -> float | None:
    """Parse the first numeric value from an ARPAE forecast field."""
    if not value:
        return None
    match = _NUMBER_RE.search(value)
    if match is None:
        return None
    return float(match.group(0).replace(",", "."))


class ArpaeWeatherClient:
    """Small async client for public ARPAE JSON endpoints."""

    def __init__(
        self,
        session: ClientSession,
        retry_delays: tuple[float, ...] = FETCH_RETRY_DELAYS,
    ) -> None:
        self._session = session
        self._retry_delays = retry_delays

    async def async_fetch_data(
        self,
        province: str,
        zone: str,
        alert_zone: str,
    ) -> ArpaeWeatherData:
        """Fetch and parse forecast and alert data."""
        forecast_json = await self._async_fetch_json(FORECAST_URL)
        alert_json = await self._async_fetch_json(ALERT_URL)
        bulletin = _latest_bulletin(forecast_json)
        forecasts = parse_bulletin(bulletin, province, zone)
        alert = parse_weather_alert(alert_json, alert_zone)
        emission = _get_nested(bulletin, "oggi", "bollettino", "emissione")
        tendency = bulletin.get("tendenza3g")
        return ArpaeWeatherData(
            forecasts=tuple(forecasts),
            alert=alert,
            tendency=tendency if isinstance(tendency, str) else None,
            emission=emission if isinstance(emission, str) else None,
        )

    async def _async_fetch_json(self, url: str) -> dict[str, Any]:
        for attempt in range(len(self._retry_delays) + 1):
            try:
                async with self._session.get(url) as response:
                    try:
                        response.raise_for_status()
                    except ClientResponseError as err:
                        if err.status in RETRY_HTTP_STATUSES:
                            raise
                        raise ArpaeWeatherError(
                            f"ARPAE endpoint {url} returned HTTP {err.status}"
                        ) from err

                    data = await response.json(content_type=None)
                break
            except JSONDecodeError as err:
                if not await self._async_backoff(attempt):
                    raise ArpaeWeatherError(
                        f"ARPAE endpoint {url} returned invalid JSON"
                    ) from err
            except ClientResponseError as err:
                if not await self._async_backoff(attempt):
                    raise ArpaeWeatherError(
                        f"ARPAE endpoint {url} returned HTTP {err.status}"
                    ) from err
            except ClientError as err:
                if not await self._async_backoff(attempt):
                    raise ArpaeWeatherError(
                        f"ARPAE endpoint {url} request failed: {err}"
                    ) from err

        if not isinstance(data, dict):
            raise ArpaeWeatherError(
                f"ARPAE endpoint {url} returned {type(data).__name__}, expected JSON object"
            )
        return data

    async def _async_backoff(self, attempt: int) -> bool:
        if attempt >= len(self._retry_delays):
            return False
        await asyncio.sleep(self._retry_delays[attempt])
        return True


def parse_bulletin(
    bulletin: dict[str, Any],
    province: str,
    zone: str,
) -> list[ForecastDay]:
    """Parse the latest ARPAE weather bulletin into daily forecasts."""
    province = province.upper()
    zone = zone.upper()
    days: list[ForecastDay] = []
    day_labels = {
        "oggi": "Oggi",
        "domani": "Domani",
        "dopodomani": "Dopodomani",
    }
    slot_names = {
        "mattina": "Mattina",
        "pomeriggio": "Pomeriggio",
        "sera_notte": "Sera/Notte",
    }

    for day_key, day_label in day_labels.items():
        bollettino = _get_nested(bulletin, day_key, "bollettino")
        if not isinstance(bollettino, dict):
            continue

        prov = _get_nested(bollettino, "provinciale", province)
        if not isinstance(prov, dict):
            continue

        slots: list[ForecastSlot] = []
        for slot_key, slot_name in slot_names.items():
            slot_data = prov.get(slot_key)
            if not isinstance(slot_data, dict):
                continue
            zone_data = slot_data.get(zone) or next(iter(slot_data.values()), None)
            if not isinstance(zone_data, dict):
                continue
            icon_code = zone_data.get("icona")
            condition = zone_data.get("it")
            if not isinstance(icon_code, str) or not isinstance(condition, str):
                continue
            slots.append(
                ForecastSlot(
                    name=slot_name,
                    condition=_format_condition(condition),
                    icon=_icon_class(icon_code),
                )
            )

        tab = _pick_zone_data(prov.get("dati_tabellari"), zone)
        days.append(
            ForecastDay(
                label=day_label,
                validita=_string_or_none(bollettino.get("validita")) or day_label,
                slots=tuple(slots),
                tmin=_find_province_value(_get_nested(bollettino, "dati", "temperatura_minima"), province)
                or _string_from_mapping(tab, "tmin_previ"),
                tmax=_find_province_value(_get_nested(bollettino, "dati", "temperatura_massima"), province)
                or _string_from_mapping(tab, "tmax_previ"),
                precipitation=_string_from_mapping(tab, "precipitazioni"),
                wind=_string_from_mapping(tab, "vento_massimo"),
                regional_sky=_string_or_none(_get_nested(bollettino, "regionale", "testo", "cielo")),
            )
        )

    return days


def parse_weather_alert(
    alert: dict[str, Any],
    alert_zone: str,
) -> WeatherAlert | None:
    """Parse active alert data for a configured alert zone."""
    zone_code = alert_zone.upper()
    zone = alert.get(zone_code)
    if not isinstance(zone, dict):
        return None

    phenomena = tuple(
        AlertPhenomenon(key=key, label=label, color=color)
        for key, label in ALERT_LABELS.items()
        if isinstance((color := zone.get(key)), str) and color in ("yellow", "orange", "red")
    )
    if not phenomena:
        return None

    color = max(phenomena, key=lambda item: ALERT_SEVERITY[item.color]).color
    return WeatherAlert(
        zone=zone_code,
        color=color,
        title=_string_or_none(alert.get("titolo")) or f"Allerta {color}",
        link=_normalize_alert_link(_string_or_none(alert.get("link"))),
        starts_at=_string_or_none(alert.get("dataInizio")),
        ends_at=_string_or_none(alert.get("dataFine")),
        description=_string_or_none(alert.get("descrizionemeteo")),
        phenomena=phenomena,
    )


def _latest_bulletin(response: dict[str, Any]) -> dict[str, Any]:
    items = response.get("_items")
    if not isinstance(items, list) or not items or not isinstance(items[0], dict):
        raise ValueError("No bulletin found in ARPAE response")
    return items[0]


def _get_nested(data: dict[str, Any], *keys: str) -> Any:
    current: Any = data
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def _icon_class(icon_code: str) -> str:
    return ICON_MAP.get(icon_code, "cloudy")


def _format_condition(condition: str) -> str:
    return condition[:1].upper() + condition[1:]


def _pick_zone_data(tabellari: Any, zone: str) -> dict[str, Any] | None:
    if not isinstance(tabellari, dict):
        return None
    if zone == "P":
        data = tabellari.get("pianura")
    elif zone == "C":
        data = tabellari.get("collina") or tabellari.get("rilievi") or tabellari.get("pianura")
    elif zone == "R":
        data = tabellari.get("rilievi") or tabellari.get("pianura")
    else:
        data = tabellari.get("pianura") or tabellari.get("collina") or tabellari.get("rilievi")
    return data if isinstance(data, dict) else None


def _find_province_value(values: Any, province: str) -> str | None:
    if not isinstance(values, dict):
        return None
    for value in values.values():
        if not isinstance(value, dict):
            continue
        description = value.get("descrizione")
        data = value.get("dato")
        if isinstance(description, str) and province in description and isinstance(data, str):
            return data
    return None


def _string_from_mapping(mapping: dict[str, Any] | None, key: str) -> str | None:
    if not mapping:
        return None
    return _string_or_none(mapping.get(key))


def _string_or_none(value: Any) -> str | None:
    return value if isinstance(value, str) else None


def _normalize_alert_link(link: str | None) -> str | None:
    if not link:
        return None
    if link.startswith(("http://", "https://")):
        return link
    return f"{ALERT_BASE_URL}{'' if link.startswith('/') else '/'}{link}"
