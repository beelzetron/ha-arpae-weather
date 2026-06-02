# ARPAE Weather

Home Assistant custom integration for ARPAE Emilia-Romagna forecasts and weather alerts.

This MVP exposes sensor entities and one daily forecast weather entity. It fetches public ARPAE JSON endpoints server-side so dashboards do not need custom frontend fetch logic.

## Scope

- YAML configuration only.
- Daily ARPAE forecast support through `weather.arpae_weather`.
- Alert and tendency metadata through sensor entities.
- No hourly forecast or nowcast support.

## Installation

Copy the integration folder into Home Assistant:

```bash
cp -R custom_components/arpae_weather /config/custom_components/arpae_weather
```

Add YAML configuration:

```yaml
arpae_weather:
  province: BO
  zone: P
  alert_zone: C2
  scan_interval:
    hours: 2
```

Restart Home Assistant.

## Configuration

| Option | Default | Description |
| --- | --- | --- |
| `province` | `BO` | Province code used for provincial forecast data. |
| `zone` | `P` | Local area type: `P` pianura, `C` collina, `R` rilievi. |
| `alert_zone` | `C2` | Allerta Meteo Emilia-Romagna alert zone. |
| `scan_interval` | `hours: 2` | Home Assistant polling interval. Keep this conservative. |

## Entities

- `sensor.arpae_weather_alert_level`
- `sensor.arpae_weather_alert_phenomena`
- `sensor.arpae_weather_today`
- `sensor.arpae_weather_tomorrow`
- `sensor.arpae_weather_day_after_tomorrow`
- `sensor.arpae_weather_tendency`
- `weather.arpae_weather`

## Clock Weather Card

The weather entity supports daily forecasts only. A tested `clock-weather-card` configuration is:

```yaml
type: custom:clock-weather-card
entity: weather.arpae_weather
title: ARPAE
temperature_sensor: sensor.gw3000a_wifife8f_outdoor_temperature
forecast_rows: 3
hourly_forecast: false
locale: it
time_format: 24
show_decimal: false
```

Use `hourly_forecast: false`; ARPAE bulletin data is daily/slot-based and does not provide true hourly forecasts. The optional `temperature_sensor` can point at a local outdoor sensor so the card header shows live measured temperature while `weather.arpae_weather` provides the forecast condition and daily rows.

## Data Use

This integration reads public ARPAE/Regione Emilia-Romagna weather and alert endpoints:

- ARPAE weather bulletin: `https://apps.arpae.it/REST/meteo_bollettini/?sort=-_id&max_results=1`
- Allerta Meteo Emilia-Romagna alert state: `https://allertameteo.regione.emilia-romagna.it/o/get-stato-allerta`

The default `scan_interval` is 2 hours, so a normal Home Assistant instance makes 12 requests per endpoint per day. Keep polling intervals conservative, do not use this integration for bulk data extraction, and attribute ARPAE/Regione Emilia-Romagna as the data source when publishing dashboards or derived data.

## MVP Scope

This first version is YAML-only and supports daily weather forecasts. It intentionally does not include a config flow, hourly forecasts, nowcast support, diagnostics, HACS metadata, or a custom card.

## Development

Install development dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

Run tests:

```bash
pytest -q
```

Clean verification with Podman:

```bash
podman run --rm -v "$PWD:/workspace:Z" -w /workspace registry.access.redhat.com/ubi9/python-312 bash -lc 'python -m venv /tmp/venv && source /tmp/venv/bin/activate && pip install -e ".[dev]" >/tmp/pip.log && pytest -q && python -m compileall -q custom_components tests'
```
