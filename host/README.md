# Host Runtime (`m5resolver`)

Python runtime that bridges telemetry and intents.

## Features

- Serial controller for device communication
- Agentic closed-loop observer with self-healing remediation
- FluxWire reactive mapping graph + MeshBus gossip state
- Simulation-in-the-loop safety gate before hardware push
- Vibe compiler (natural language -> intent JSON)
- Vibe-IDE web gateway (WebSerial in browser)
- Dynamic JSON-backed unit registry (Hardware Context Protocol)
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

Validate intent without sending:

```bash
m5resolver --port COM3 --intent-file ./sample-intent.json --dry-run
```

## Vibe-IDE server

```bash
m5vibe --host 127.0.0.1 --port 8023
```

Then open `http://127.0.0.1:8023` and use WebSerial connect + vibe prompt injection.
