# ADR 0040: Unified m5-kernel Integration Entry Point

## Status

Accepted — 2026-05-29

## Context

The m5-utah stack accumulated many SOTA modules (CrossCorePipe, HandleMemory,
PriorityGatekeeper, BusArbitrator, ResourceOrchestrator, mesh sync, CI pipeline).
Contributors need one documented boot path and lifecycle map — not duplicate FreeRTOS
tasks in `main.cpp`.

## Decision

### Firmware

- `m5IntegratedKernelBoot()` in `M5IntegratedKernel.cpp` — single call from `setup()`
- Order: `registryRuntimeInit()` → subsystem inits → `M5Kernel::start()`
- `main.cpp` retains JSON/binary dispatch helpers and suspended `loop()`

### Host

- `INTEGRATED_BOOT_SEQUENCE` and `UNIFIED_LIFECYCLE_STAGES` in `kernel_runtime.py`
- `test_m5_unified_lifecycle_boot_sequence` validates documentation contract

### Documentation

- `docs/en/architecture.md` — unified lifecycle mermaid + boot table

## Consequences

- Explicit rejection of ad-hoc Core 0 `Serial.readBytes` ring templates in main
- No behavioral change to CrossCorePipe demux or M5Kernel dispatch logic
