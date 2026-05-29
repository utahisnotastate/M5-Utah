# ADR 0024: Telemetry-Driven Self-Healing Diagnostic Loops

## Status

Accepted — 2026-05-29

## Context

Manual telemetry monitoring cannot keep pace with heap drift, scheduling jitter, or bus timing slip
on constrained ESP32 nodes. ADR 0002 (thin firmware boundary) and ADR 0003 (registry-driven units)
enable the host to synthesize corrective intents from structured device telemetry rather than
requiring developer intervention.

## Decision

### Feature 53 — Self-Synthesizing Telemetry-Driven Diagnostic Loops

**Firmware**

- `TelemetryHealth` tracks active fast-path unit/pin and orchestration jitter
- `emitTelemetry()` publishes `task_jitter_ms`, `active_unit_id`, `active_pin`
- Degraded nodes additionally emit `[TELEMETRY_STREAM]:` prefixed JSON for host intercept

**Host**

- `AutonomousMitigationEngine` in `mitigation_engine.py`, wired through `IntentController._process_frame()`
- On heap `< 25KB` or jitter `> 50ms`, validates and injects binwire throttle patch (`##` frame)
- 2-second cooldown prevents remediation storms

## Consequences

- Capability: `telemetry_self_healing_loop`
- Closed loop: telemetry → host anomaly detection → fast-path corrective binwire → firmware apply
- Complements (does not replace) `AgenticController.observe_and_correct()` JSON corrective intents
