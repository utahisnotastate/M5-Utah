# ADR 0039: Multi-Stage CI/CD Validation Pipeline (m5-pipeline)

## Status

Accepted — 2026-05-29

## Context

The m5-utah stack spans Python host orchestration, 149+ pytest contracts, and ESP32
dual-core firmware. Community PRs require automated gates before merge to prevent
cross-platform wire-format drift and firmware regressions.

## Decision

### `.github/workflows/m5utah-ci.yml`

Two parallel jobs:

1. **validate-host-plane** — `pip install -e host`, flake8 critical errors, JSON artifact
   parse, full `pytest tests/`, scheduler/delta compiler smoke checks
2. **validate-firmware-core** — PlatformIO build for `m5stack-cores3` and `m5stack-core-esp32`

### `firmware/platformio.ini`

- `default_envs = m5stack-cores3`
- `-O3`, `CORE_DEBUG_LEVEL=3`
- Dual targets: `m5stack-cores3` (primary) and `m5stack-core-esp32` (reference CI matrix)
- `ArduinoJson@^7.0.4` + `M5Unified@^0.2.7`

Minor firmware header/ cast fixes enable clean PlatformIO builds on CI runners.

### Coexistence

- Existing `ci.yml` (ruff/mypy) and `schema-check.yml` remain; `m5utah-ci.yml` is the
  canonical multi-stage pipeline for main/master PR gates.

## Consequences

- PRs to main/master run host + firmware matrices concurrently
- No black gate (repo not black-formatted); flake8 E9/F63/F7/F82 enforced instead
