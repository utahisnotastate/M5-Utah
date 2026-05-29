# ADR 0014: DAG State Graph and Bitmapped Delta Compression

## Status

Accepted — 2026-05-29

## Context

Flat registry maps force full hot-reloads across mesh nodes. Streaming uncompressed JSON
for hundreds of virtual units saturates Fluxwire gossip channels. Structural dependencies
(DSP pipelines, sensor→actuator chains) need minimal mutation trees and compact wire format.

## Decision

### Feature 30 — StateGraphEngine (host)

- Registry units form a DAG via `depends_on` edges.
- `compute_mutation_delta_paths()` returns downstream cascade for a changed root.
- `validate_dag()` rejects unknown dependencies and cycles before deploy.

### Feature 31 — DeltaEngine (firmware + host)

- Wire format: magic `0xDE 0xDA` + sequence byte + 16-bit slot bitmask + per-slot `uint16` Hz.
- Firmware applies slots via `registryApplyDeltaSlot()` without JSON parsing.
- `DeltaEncoder.encode_graph_mutation()` compiles graph cascades to bitmask frames.

### Feature 32 — Dependency validation tests

- Graph cycle detection in `tests/test_validation.py` and `tests/test_graph_engine.py`.

## Consequences

- `DriverRegistry.load()` exposes `graph` and `last_graph_errors`.
- Delta frames bypass crypto JSON envelope (binary fast path like binwire).
- Maximum 16 simultaneous structural slots (`slot_id` 0–15).

## References

- ADR 0008 Binwire Fast-Path Serialization
- ADR 0013 Resource Pruning and Speculative Staging
- `host/m5resolver/graph_engine.py`
- `firmware/src/DeltaEngine.h`
