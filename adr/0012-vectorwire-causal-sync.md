# ADR 0012: Vector Clock Causal Synchronization (m5-vectorwire)

## Status

Accepted — 2026-05-29

## Context

Multi-node m5-utah meshes cannot rely on NTP or wall-clock timestamps over lossy wireless
links. Concurrent IMU events, button interrupts, and registry cascades need deterministic
partial ordering without a central time authority.

## Decision

### Feature 24 — VectorClockTracker (host)

- Per-node logical counters in `vector_clock.py`.
- `merge_and_verify_causality()` detects gaps (`incoming > local + 1`).
- `FluxGraph.ingest_telemetry_causality()` suppresses intent patches on violation and buffers
  frames for re-sequencing.

### Feature 25 — VectorTelemetryBuilder (firmware)

- Embeds `sender_id` and `vector_clocks` in telemetry and hardware events.
- Host may push `vector_clock_sync` intents to update firmware host-clock mirror.

### Feature 26 — Automated verification

- Causal bound tests in `tests/test_fluxwire.py` and `tests/test_vector_clock.py`.
- `schemas/telemetry.schema.json` documents `vector_clocks` and `sender_id`.

## Consequences

- Legacy telemetry without `vector_clocks` remains accepted (backward compatible).
- Causal suppression prevents out-of-order agent remediation loops.
- Vector clocks track logical order, not physical simultaneity.

## References

- ADR 0009 Raft Consensus and Sandboxing
- `host/m5resolver/vector_clock.py`
- `firmware/src/VectorTelemetry.h`
