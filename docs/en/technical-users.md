# Technical User Guide

## Stack overview (v0.8.2)

| Component | Path | Role |
|-----------|------|------|
| Utah Flux Studio | `host/utah_flux/studio.py` | Lego brick GUI (port 8765) |
| **UtahClaw canvas** | `host/utah_flux/static/utah_studio.html` | Intent-resolution UI (port 8024) |
| **Omniscient deck** | `host/utah_flux/omniscient_daemon.py` | Auto-discovery (port 8000) |
| UtahClaw daemon | `host/utah_flux/utahclaw_daemon.py` | Ollama + serial bridge |
| Field graph compiler | `host/utah_flux/field_compiler.py` | Sanctum `nodes`/`bindings` → display intents |
| m5resolver | `host/m5resolver/` | Intents, typestate, secure wire, agent |
| Omega defense | `firmware/src/OmegaDefense.*` + six modules | Edge resiliency stack |
| Sovereign edge | `firmware/src/SovereignEdge.*` + Acoustic/Matrix/Swarm | Declarative runtime tier |
| Immortal firmware | `firmware/src/ImmortalDiscovery.*` | I2C scan on Core 0 |
| Firmware kernel | `firmware/` | Dual-core M5Kernel runtime |

## User vs developer paths

- **Children / makers:** `Start Utah Flux Studio.bat`
- **Vibe-coding engineers:** `Install UtahClaw.bat` → `Start UtahClaw Studio.bat` + Ollama
- **Discovery demos:** `launch/Start Omniscient Studio.bat`
- **Developers:** `pip install -e host`, `pytest`, `examples/`
- **Sanctum field graphs:** `projects/sanctum.flux.json` + `field_compiler.py` (see [field-graph-compiler.md](field-graph-compiler.md))

## Full tutorial

See [Technical Tutorial](tutorials/technical-tutorial.md).

## Intent model

Keys: `display`, `speaker`, `power`, `registry`, `capability_query`, `ephemeral_store`  
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
