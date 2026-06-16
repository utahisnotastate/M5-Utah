# ADR 0044: Immortal Bootloader and Autonomic I2C Discovery

## Status

Accepted — 2026-05-29

## Context

End users should flash firmware once and never repeat the cycle for functional updates.
Grove sensors must appear in the studio UI without manual driver configuration or
hardcoded `Wire.begin()` assumptions.

## Decision

### Firmware — Immortal Discovery

- `ImmortalDiscovery.{h,cpp}` — FreeRTOS task pinned to Core 0 (priority 1)
- Polls I2C addresses `0x01`–`0x7E` every 500ms on Grove Port A
- Emits JSON `discovery` / `disconnect` events on Serial
- Initialized from `m5IntegratedKernelBoot()` after health harvester
- Does not replace CrossCorePipe protocol ingest or M5Kernel orchestration

### Host — Zero-friction daemons

- `host/utah_flux/hardware_matrix.py` — Espressif VID `303A` auto-scan, registry merge
- `host/utah_flux/omniscient_daemon.py` — WebSocket GUI on port 8000
- `host/utah_flux/utahclaw_daemon.py` — Ollama vibe-coding + error heal on port 8024
- Optional deps: `pip install -e 'host[daemon]'` or `host[claw]`

### WebSerial

Utah Flux Studio continues to support browser `navigator.serial` for driverless Chromium
sessions; Python daemons complement offline/auto-scan workflows.

## Consequences

- One-time factory flash ships the immortal kernel; intents update behavior via JSON
- I2C scan coexists with BusArbitrator; scan uses standard 100kHz
- UtahClaw requires local Ollama (`ollama run llama3`); graceful error if missing
