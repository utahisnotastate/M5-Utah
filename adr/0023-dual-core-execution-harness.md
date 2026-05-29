# ADR 0023: Dual-Core Non-Blocking Execution Harness

## Status

Accepted — 2026-05-29

## Context

High-volume serial ingest on a single thread blocks peripheral scheduling and causes timing drift on
motor drivers, display timers, and sensor interrupts. Feature 52 formalizes the production dual-core
layout already introduced by M5Kernel and CrossCorePipe (ADR 0016, ADR 0020).

## Decision

### Feature 52 — Dual-Core Non-Blocking Execution Harness

| Core | Engine | Responsibility |
|------|--------|----------------|
| **0** | Protocol ingestion | Serial demux, `##`/`0xDE`/`#M` intercept, non-blocking ring push |
| **1** | Application execution | Ring drain, binwire/JSON dispatch, hardware orchestration — no blocking Serial I/O |

Implementation surfaces:

- `firmware/src/DualCoreHarness.h` — wire layout (`DirectHardwareCommand`), ring sizing constants
- `CrossCorePipe` — FreeRTOS `RINGBUF_TYPE_NOSPLIT` ring; ingest task priority **3** on Core 0
- `M5Kernel` — Core 1 application loop drains ring via `dispatchPipeFrame()`
- Registry `fast_path_bridge` units with `execution_core_target` and `buffer_allocation_bytes`
- Host `dual_core_harness.py` validation mirror

`main.cpp` retains `M5Kernel::start()` + suspended `loop()` — **not** replaced by ad-hoc ring tasks.

## Consequences

- Capability: `dual_core_execution_harness`
- Minimum ring allocation contract: 512 bytes; production ring: 8192 bytes
- Regression: `test_cross_core_execution_schema_contracts` in `tests/test_registry.py`
