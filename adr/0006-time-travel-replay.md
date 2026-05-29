# ADR 0006: Time-Travel State Journaling and Replay

- Status: accepted
- Date: 2026-05-28

## Context

Embedded debugging often requires JTAG and hard-to-reproduce transient failures. Our intent-first registry model makes state transitions deterministic and serializable.

## Decision

1. Firmware maintains a rolling `TimeTravelJournal` of intent fingerprints and heap metrics.
2. On low-heap or ACK errors, firmware emits `[FLUXWIRE_TIME_TRAVEL_STREAM]:{json}`.
3. Host `HostReplayEngine` replays journal offline to identify fault fingerprints.
4. `IntentController` intercepts journal streams automatically.

## Consequences

- Faster root-cause analysis without physical debugger attachment.
- Journal dumps integrate with Utah Flux Studio Live Log.
- CI runs replay tests to guard regression detection logic.
