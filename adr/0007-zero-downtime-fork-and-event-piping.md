# ADR 0007: Zero-Downtime State Forking and Virtual Event Piping

## Status

Accepted — 2026-05-29

## Context

Registry hot-reload previously called `clearUnitTasks()` and deleted every FreeRTOS worker before
rebuilding units. That caused execution gaps (PWM cutoffs, floating GPIO, dropped semantic loops).

Host-side hardware interactions were also tightly coupled: button pins and LED outputs had no
decoupled routing layer for vibe-driven intent patches.

## Decision

### Feature 9 — StateForker (firmware)

- Introduce `StateForker` with a bounded pool (`kMaxPool = 10`) tracking `ForkedUnit` records.
- On hot reload, differentially fork changed units via shadow task creation, priority swap, and
  graceful deletion of the predecessor task.
- Units carry `refresh_sequence_id` in registry payloads for deterministic swap ordering.
- Full teardown only when `safeguard: true` is set (low heap / brownout protection).

### Feature 10 — VirtualEventRouter (host)

- Add `host/m5resolver/events.py` with `register_intent_pipe()` and `ingest_hardware_signal()`.
- Wire `IntentController.read_frame()` to multiplex `event_type` / `hardware_event` frames.
- Default routes map `button_click_event` → LED intent and `motion_spike_event` → alert intent.

### Feature 11 — Registry lifecycle contracts (tests)

- Extend `UnitSpec.refresh_sequence_id` and pytest coverage for fork lifecycle serialization.

## Consequences

- Hot registry patches no longer require full task teardown unless safeguard triggers.
- Physical peripherals emit virtual events over Fluxwire; host routes them without C++ coupling.
- Shadow swap uses FreeRTOS priority elevation — callers must keep unit workers idempotent.

## References

- ADR 0002 Thin Firmware Boundary
- ADR 0003 Registry-Driven Unit Model
- `firmware/src/StateForker.h`
- `host/m5resolver/events.py`
