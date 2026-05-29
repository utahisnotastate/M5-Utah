# ADR 0019: Priority-Inheritance Gatekeeper and Scheduler Compiler

## Status

Accepted — 2026-05-29

## Context

Dynamic FreeRTOS units competing for shared I2C/SPI buses and registry assets risk priority
inversion when low-priority tasks hold mutexes needed by realtime control loops. Reactive
FreeRTOS priority inheritance alone may stall high-priority work before elevation occurs.

## Decision

### Feature 45 — PriorityGatekeeper (firmware)

- Four guarded assets: I2C bus, SPI bus, registry flash, crypto block.
- Proactive priority boost before mutex acquisition; restore after release.
- `DynamicMultiplexer` routes bus hot-swap through gatekeeper then TDMA arbitrator fallback.

### Feature 46 — HostSchedulerCompiler (host)

- Pin-contention audit across registry units with `realtime_critical` escalation.
- Injects `assigned_priority_tier` (1–3) before wireless deploy via `send_intent()`.
- Maps tiers to firmware FreeRTOS priority levels.

### Feature 47 — Scheduling validation tests

- Priority tier schema validation and conflict elevation contract tests.

## Consequences

- Capability: `priority_inheritance_gatekeeper`.
- Registry fields: `realtime_critical`, `assigned_priority_tier`.
- Telemetry metrics: `gatekeeper_boost_count`, `gatekeeper_lock_count`.
