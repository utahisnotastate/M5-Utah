# Technical User Guide

## What this is

M5 Resolver Substrate consolidates M5Stack development into:

- one universal firmware runtime
- one host runtime (`m5resolver`)
- one registry (`registry/units.json`)
- one intent-driven control model

## Quick start

1. Flash firmware in `firmware/`
2. Install host package from `host/`
3. Run `python examples/tilt_tone.py --port COM3`

## Intent model

Supported intent top-level keys:

- `display`
- `speaker`
- `power`

Contracts are defined in `schemas/intent.schema.json`.

## Development guidance

- Keep firmware deterministic and minimal.
- Move behavior logic into host-side mappings.
- Add unit metadata to registry rather than creating per-device forks.

## Vibe-IDE and agentic loop

- Start gateway: `m5vibe`
- Browser compiles natural language via `/generate_intent`
- `AgenticController` validates, simulates, and can auto-remediate telemetry anomalies
- Firmware hot-reloads `registry` payloads without reflashing C++ behavior
