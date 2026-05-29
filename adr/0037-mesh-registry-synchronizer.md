# ADR 0037: Mesh Registry Synchronizer (2PC)

## Status

Accepted — 2026-05-29

## Context

Multi-node vibe deployments risk split-brain registry drift. ADR 0012 introduced
Raft consensus; this ADR adds explicit two-phase commit orchestration on the host
with firmware heap feasibility votes before registry hot-reload.

## Decision

### Host — `MeshStateSynchronizer`

- Phase 1: `query_node_readiness()` on every cluster node
- Phase 2: `broadcast_commit_token()` when all nodes approve
- Integrates `StateGraphEngine.validate_dag()` and optional `DeltaEncoder` commit frames
- `IntentController.send_cluster_registry_mutation()` via `ControllerClusterTransport`

### Firmware — `TransactionalCoreManager`

- `transaction_prepare` JSON → `transaction_vote` response with heap headroom check (30%)
- `transaction_commit` + `registry` → feasibility gate before `registryHotReload()`
- No replacement of dual-core task architecture

## Consequences

- Capability: `mesh_registry_synchronizer`
- Tests: `test_mesh_two_phase_commit_safety`, `test_mesh_two_phase_commit_success`
- Complements `HardwareConsensusCluster` leader commit path
