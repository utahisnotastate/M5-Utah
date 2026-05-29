# ADR 0013: Resource-Aware Intent Pruning and Speculative Staging

## Status

Accepted — 2026-05-29

## Context

Complex vibe-coded intents (high-rate ADC, FFT, mesh streaming) can exhaust ESP32 heap and
stall multi-node clusters. Hot-reload task swaps need dry-run validation before promotion to
avoid glitches during configuration cascades.

## Decision

### Feature 27 — HardwareCostModel (host)

- Deterministic RAM estimate: `buffer_size * 2 + frequency_hz * 4`.
- Prune when draw exceeds 40% of reported free heap (`HEADROOM_RATIO`).
- `IntentController.send_intent()` auto-prunes using live telemetry `metrics.free_heap`.

### Feature 28 — SpeculativeStagingBuffer (firmware)

- Shadow tasks run at elevated priority for `verificationTimeoutMs` (default 200 ms).
- Heap monitored each 50 ms tick; failure deletes shadow and reverts via stable snapshot.
- `StateForker` routes all spawns through `speculativeSpawnUnit()`.

### Feature 29 — Optimization tests

- `tests/test_registry.py` and `tests/test_optimizer.py` validate pruning bounds.

## Consequences

- Pruned intents carry `pruned_by_gatekeeper` and top-level `resource_pruned` flags.
- Staging adds ~200 ms latency to new unit promotion (acceptable vs. crash recovery).
- Without telemetry, host assumes 32 KB default heap budget.

## References

- ADR 0007 Zero-Downtime State Forking
- ADR 0012 Vectorwire Causal Sync
- `host/m5resolver/optimizer.py`
- `firmware/src/SpeculativeStaging.h`
