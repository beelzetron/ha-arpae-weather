# Repository Guidelines

## Project Structure & Module Organization

This repository contains a Home Assistant custom integration for ARPAE Emilia-Romagna forecasts and alerts. Integration code lives in `custom_components/arpae_weather/`:

- `__init__.py` registers YAML configuration and platform setup.
- `api.py` handles ARPAE endpoint fetching and response parsing.
- `coordinator.py` contains update coordination.
- `sensor.py` defines exposed Home Assistant sensor entities.
- `weather.py` defines the daily forecast `WeatherEntity`.
- `const.py` and `manifest.json` hold integration constants and metadata.

Tests live in `tests/`, currently focused on parser and weather forecast mapping behavior in `tests/test_api.py`. User-facing setup notes are in `README.md`.

## Build, Test, and Development Commands

Create a local Python environment before installing dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

Run the test suite with:

```bash
pytest -q
```

Run a focused test file while iterating:

```bash
pytest tests/test_api.py
```

Run clean verification with Podman:

```bash
podman run --rm -v "$PWD:/workspace:Z" -w /workspace registry.access.redhat.com/ubi9/python-312 bash -lc 'python -m venv /tmp/venv && source /tmp/venv/bin/activate && pip install -e ".[dev]" >/tmp/pip.log && pytest -q && python -m compileall -q custom_components tests'
```

For manual Home Assistant testing, copy the integration into a Home Assistant config directory:

```bash
cp -R custom_components/arpae_weather /config/custom_components/arpae_weather
```

Then configure the `arpae_weather:` YAML block as shown in `README.md`.

## Coding Style & Naming Conventions

Use Python 3.12 syntax and standard Home Assistant async patterns. Keep indentation at four spaces. Use `snake_case` for functions, variables, and test names; use `PascalCase` for classes; keep constants uppercase in `const.py`. Prefer typed dataclasses or explicit parser helpers when shaping ARPAE payloads, and keep network access separate from pure parsing logic so tests stay fast.

## Testing Guidelines

Tests use `pytest`. Name tests `test_<behavior>` and keep fixtures or builders local when they are only used by one file, as in `make_bulletin()`. Add parser tests for malformed, missing, or alternate ARPAE fields before changing parsing behavior. Run `pytest` before opening a PR.

## Commit & Pull Request Guidelines

Use concise imperative commit subjects, for example `Add alert severity parser tests`. Pull requests should describe the behavior change, list validation commands, and call out Home Assistant configuration or entity changes. Include screenshots only when sensor presentation or dashboard examples change.

## Security & Configuration Tips

Do not commit Home Assistant secrets, tokens, or private `/config` files. Keep `manifest.json` metadata aligned with `pyproject.toml` version changes, and avoid adding runtime dependencies unless they are required by Home Assistant or the integration.

## External Data Use

The default `scan_interval` is 2 hours. Keep polling conservative and do not add bulk extraction behavior. ARPAE bulletin data is daily/slot-based; do not add hourly or nowcast forecast entities unless the source data actually supports that behavior.
