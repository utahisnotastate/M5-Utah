# ADR 0027: Integrated Asymmetric m5-kernel Completion

## Status

Accepted — 2026-05-29

## Context

Distributed edge workloads (Python host, Android companion, Fluxwire mesh) can saturate serial
ingress and cause priority inversion when FreeRTOS tasks compete for I2C/SPI/registry locks.
The repository already implements the user's requested architecture across dedicated modules;
this ADR formalizes the integrated runtime and forbids regressing `main.cpp` to ad-hoc ring tasks.

## Decision

### Integrated m5-kernel module graph

| Concern | Module | Core |
|---------|--------|------|
| Lock-free ring ingest | `CrossCorePipe` | 0 |
| Orchestration loop | `M5Kernel` | 1 |
| Priority inversion prevention | `PriorityGatekeeper` | 1 |
| TDMA bus windows | `BusArbitrator` | 1 |
| Virtual handles / compaction | `HandleMemoryManager` | 1 |
| Pressure deferral | `ResourceOrchestrator` | 1 |
| Host priority tiers | `HostSchedulerCompiler` | host |

`M5IntegratedKernel.h` documents the single entry-point header. Boot remains
`registryRuntimeInit()` + `M5Kernel::start()`.

### Enhancements (this change)

- RPP `#P` dispatch on Core 1 routes through `PriorityGatekeeper` (proactive boost + mutex)
- `scheduler_compiler.py` self-test harness under `__main__`
- Contract tests for scheduler + kernel integration

## Consequences

- Do **not** replace production firmware with standalone `xRingbufferCreate` tasks in `main.cpp`
- `IntentController.send_intent()` continues auto-applying `HostSchedulerCompiler.apply_to_intent()`
- Regression: `test_automated_priority_elevation_contracts`, `test_m5_integrated_kernel_contracts`
