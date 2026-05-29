# ADR 0034: Hot-Swappable IRAM Vector Fence (m5-vectorfence)

## Status

Accepted — 2026-05-29

## Context

High-frequency vibe features (motor control, sub-ms ADC) cannot rely solely on Core 1
task loops. ADR 0015 introduced `#M` IRAM overlays at fixed addresses; this ADR adds
channel-indexed ISR hot-patching with atomic vector pointer swaps.

## Decision

### Host — `HostVectorCompiler`

- Wire magic: `#I` (`0x23 0x49`), header `!BHI` + machine-code payload (max 512 bytes)
- `compile_vector_overlay()` metadata-only; `compile_vector_patch()` full wire frame
- `IntentController.send_vector_fence_patch()` and orchestrator `synchronize_vector_fence()`

### Firmware — `VectorFenceEngine`

- Four virtual interrupt channels with `MALLOC_CAP_EXEC` IRAM pools
- Atomic `portDISABLE_INTERRUPTS()` pointer swap into `g_dynamicIsrVectorTable[]`
- Core 0 CrossCorePipe demux → ring → Core 1 `processPayload()`

## Consequences

- Capability: `hot_swappable_vector_fence`
- Test: `test_interrupt_vector_packing_contracts`
- Complements `#M` MemoryOverlayDecoder and RuntimeLinker JIT paths
