# ADR 0009: Raft Consensus Routing and Hardware Sandboxing

## Status

Accepted — 2026-05-29

## Context

Multi-node M5Stack deployments suffer split-brain registry writes and single-node faults
propagating across the mesh. Dynamic vibe-coded units can also exhaust stack memory and
panic the entire firmware image.

## Decision

### Feature 15 — HardwareConsensusCluster (host)

- Lightweight Raft-inspired election and replicated registry log in `consensus.py`.
- `FluxGraph.commit_cluster_registry()` gates mutations on leader authorization.
- Committed state propagates through `MeshBus` and `FluxwireGossipMesh`.
- `IntentController` optional `enable_consensus` with automatic election on registry send.

### Feature 16 — Sandbox isolation (firmware)

- Static-stack sandbox slots (`Sandbox.cpp`) with high-water-mark monitoring.
- Violations trigger time-travel journal entry, task teardown, and stable snapshot revert.
- `StateForker` spawns all unit workers through `spawnSandboxedUnit()`.

### Feature 17 — Regression matrix

- Consensus election and leader-gating tests in `tests/test_fluxwire.py` and `tests/test_consensus.py`.

## Consequences

- Registry mutations on clustered hosts require leader quorum semantics.
- Sandboxed tasks use fixed 1 KB static stacks; deep recursion in unit logic will self-terminate.
- True ESP32 MPU regions are not enabled; containment uses FreeRTOS static stacks and watchdog thresholds.

## References

- ADR 0005 Dynamic Bus and Gossip Mesh
- ADR 0007 Zero-Downtime State Forking
- `host/m5resolver/consensus.py`
- `firmware/src/Sandbox.h`
