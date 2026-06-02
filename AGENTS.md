# Repository Guidelines

## Project Structure & Module Organization

This repository contains a Home Assistant custom integration for ARPAE Emilia-Romagna forecasts and alerts. Integration code lives in `custom_components/arpae_weather/`:

- `__init__.py` registers YAML configuration and platform setup.
- `api.py` handles ARPAE endpoint fetching and response parsing.
- `coordinator.py` contains update coordination.
- `sensor.py` defines exposed Home Assistant sensor entities.
- `const.py` and `manifest.json` hold integration constants and metadata.

Tests live in `tests/`, currently focused on parser behavior in `tests/test_api.py`. User-facing setup notes are in `README.md`.

## Build, Test, and Development Commands

Create a local Python environment before installing dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

Run the test suite with:

```bash
pytest
```

Run a focused test file while iterating:

```bash
pytest tests/test_api.py
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

This checkout does not include local Git history, so no repository-specific commit convention is available. Use concise imperative commit subjects, for example `Add alert severity parser tests`. Pull requests should describe the behavior change, list validation commands, and call out Home Assistant configuration or entity changes. Include screenshots only when sensor presentation or dashboard examples change.

## Security & Configuration Tips

Do not commit Home Assistant secrets, tokens, or private `/config` files. Keep `manifest.json` metadata aligned with `pyproject.toml` version changes, and avoid adding runtime dependencies unless they are required by Home Assistant or the integration.
