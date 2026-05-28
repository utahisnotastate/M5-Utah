# Host Runtime (`m5resolver`)

Python runtime that bridges telemetry and intents.

## Features

- Serial controller for device communication
- FluxWire reactive mapping graph
- Dynamic JSON-backed unit registry
- CLI for sending intents and watching telemetry

## Install

```bash
python -m venv .venv
. .venv/bin/activate  # PowerShell: .venv\Scripts\Activate.ps1
pip install -e .
```

## CLI examples

Watch telemetry:

```bash
m5resolver --port COM3 --watch
```

Send intent:

```bash
m5resolver --port COM3 --intent "{\"display\":{\"clear\":true}}"
```
