# M5 Resolver Substrate

Unified M5Stack development workspace with:

- A single firmware image ("dumb terminal") that exposes core hardware capabilities through JSON intents.
- A host-side Python runtime ("intent-resolution substrate") that handles telemetry, routing, and dynamic unit loading.
- A registry-driven driver model for M5Stack Units to reduce one-library-per-device sprawl.

## Product value

- Consolidates fragmented module-first development into one intent-first platform.
- Speeds prototyping by moving behavior iteration to host-side Python.
- Reduces duplication by centralizing hardware metadata in a shared registry.
- Improves maintainability with tests, CI, templates, and contributor docs.

## Why this exists

The M5Stack ecosystem has many independent repositories and drivers. This project provides one practical consolidation point:

- one firmware target
- one host runtime
- one extensible registry format
- one development workflow

## Repository layout

- `firmware/` PlatformIO project for M5Unified + ArduinoJson terminal firmware
- `host/` Python package (`m5resolver`) with controller, FluxWire graph, and CLI
- `registry/` JSON capability and register map definitions for Units
- `examples/` end-to-end host scripts
- `docs/` bilingual audience documentation and migration playbook
- `tests/` host runtime test suite
- `.github/` CI pipeline and contribution templates

## Quick start

### 1) Flash firmware

```bash
cd firmware
pio run -t upload
```

### 2) Install host runtime

```bash
cd host
python -m venv .venv
. .venv/bin/activate  # Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -e .
```

### 3) Run sample

```bash
cd ..
python examples/tilt_tone.py --port COM3
```

## Design principles

- Intent-first API: describe desired state, not register-level imperative steps.
- Reactive dataflow: map telemetry to intents using composable wires.
- Registry-first drivers: declare capabilities and protocol details in JSON.
- Fast iteration loop: host-side logic updates without reflashing firmware.

## Quality and governance

- Automated host tests via GitHub Actions (`.github/workflows/ci.yml`)
- Contribution standards (`CONTRIBUTING.md`)
- Security reporting policy (`SECURITY.md`)
- Code of conduct (`CODE_OF_CONDUCT.md`)
- MIT licensing (`LICENSE`)

## Safety and scope

This code intentionally avoids unsafe runtime source mutation. Self-healing is implemented as bounded fault handling and recovery hooks, not code rewriting.
