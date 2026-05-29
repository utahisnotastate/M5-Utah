# ADR 0017: Virtual Handle Memory and Predictive Heap Compaction

## Status

Accepted — 2026-05-29

## Context

Continuous registry mutations, binary fast-paths, and event pipes fragment the ESP32 heap.
Raw pointers into relocated configuration blocks become dangling after compaction, causing
hard faults even when total free memory appears sufficient.

## Decision

### Feature 39 — HandleMemoryManager (firmware)

- Static 2048-byte pool with 32-slot virtual handle table.
- `bindHandle()` for deterministic `allocation_handle_id` from registry units.
- `compactMemoryPool()` shifts unlocked handles; locked task buffers stay pinned.
- Supervisor tick triggers predictive compaction at 92% pool utilization.
- Telemetry exports `handle_pool_top`, `handle_fragmentation_index`, `handle_active_count`.

### Feature 40 — HostMemoryProfiler (host)

- Simulates handle-pool footprint from telemetry + incoming unit `buffer_size_bytes`.
- `IntentController.preflight_memory_for_intent()` blocks unsafe registry pushes.
- Auto-issues `memory_compact` intent before retry when serial link is open.

### Feature 41 — Handle allocation validation (tests)

- Registry units may declare `allocation_handle_id` (0–31) and `buffer_size_bytes` (≤512).
- Duplicate handle slots rejected on host before wire transmit.

## Consequences

- Capabilities: `virtual_handle_memory`, `predictive_heap_compaction`.
- `UnitTaskConfig` carries handle id and buffer size for forked units.
- Compaction skips locked handles — units must unlock on teardown in future hardening.
