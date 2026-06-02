# Contributing

## Development Setup

Use Python 3.12 or newer.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Verification

Run the test suite before opening a pull request:

```bash
pytest -q
```

For a clean environment, run the same checks in Podman:

```bash
podman run --rm -v "$PWD:/workspace:Z" -w /workspace registry.access.redhat.com/ubi9/python-312 bash -lc 'python -m venv /tmp/venv && source /tmp/venv/bin/activate && pip install -e ".[dev]" >/tmp/pip.log && pytest -q && python -m compileall -q custom_components tests'
```

## Scope

Keep changes focused on the ARPAE Home Assistant integration. Prefer parser tests for changes to ARPAE response handling, and keep Home Assistant platform code thin around tested pure helpers.

This integration intentionally supports daily forecasts only. ARPAE bulletin data is daily/slot-based and should not be represented as true hourly or minute-level nowcast data without clear source data to support it.

## Data Use

Keep polling intervals conservative. The default `scan_interval` is 2 hours and should not be reduced without a clear need.

## Coding Agent Assistance

This repository may use coding agents to help draft code, tests, and documentation. Contributors are responsible for reviewing generated changes, verifying behavior, and ensuring submitted code is appropriate for the project.
