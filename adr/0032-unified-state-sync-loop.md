# ADR 0032: Complete State Synchronization Loop Matrix

## Status

Accepted — 2026-05-29

## Context

Individual SOTA layers (vibe gateway, scheduler audit, bitmapped deltas, dual-core
harness) needed a single host orchestration entry point that traces intent from
schema validation through binary overlay emission on Fluxwire.

## Decision

### `UnifiedOrchestrationController`

- Validates blocks via `IntentValidator.validate()`
- Runs `HostSchedulerCompiler.compute_priority_matrix()` preflight
- Emits `##D` frames through any transport exposing `write()` (serial, mock, mesh)
- `IntentController.unified_orchestrator()` binds to the active serial link

### End-to-end path

1. Vibe / IDE → host orchestrator
2. Graph + scheduler + validator → optimized units block
3. `BitmappedDeltaCompiler` → 10-byte wire frame
4. Core 0 CrossCorePipe demux → ring buffer
5. Core 1 `DeltaEngine` → virtual handle / registry slot hot-patch

## Consequences

- Capability: `unified_state_sync_loop`
- Test: `test_unified_orchestration_synchronization_lifecycle`
- Complements (does not replace) `IntentController.send_intent()` JSON/binwire path
