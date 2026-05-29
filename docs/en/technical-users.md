# Technical User Guide

## Stack overview (v0.3+)

| Component | Path | Role |
|-----------|------|------|
| Utah Flux Studio | `host/utah_flux/studio.py` | Browser GUI, primary UX |
| Utah-Flux library | `host/utah_flux/` | Bricks, compiler, templates |
| m5resolver | `host/m5resolver/` | Intents, safety, agent, registry ops |
| Firmware | `firmware/` | Device runtime + registry supervisor |
| Schemas | `schemas/` | Hardware Context Protocol contracts |

## User vs developer paths

- **End users:** `Start Utah Flux Studio.bat` only
- **Developers:** `pip install -e host`, `pytest`, optional `examples/agent_loop.py`

## Full tutorial

See [Technical Tutorial](tutorials/technical-tutorial.md).

## Intent model

Keys: `display`, `speaker`, `power`, `registry`, `capability_query`  
Schema: `schemas/intent.schema.json`

## Safety and simulation

All compiled projects pass:

1. `validate_intent_payload`
2. `validate_intent_safety`
3. `HardwareSimulator.simulate_intent`

## Agentic loop

`AgenticController` watches telemetry and can push corrective intents (thermal throttle, safe mode).

## API endpoints (studio)

- `GET /api/bricks` — brick catalog
- `GET /api/templates` — starters
- `POST /api/compile` — project → intent + wires

## Legacy CLI tools

`m5resolver` CLI and `examples/*.py` remain for automation; not required for product users.
