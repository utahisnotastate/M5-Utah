# ADR 0020: m5 Central Processing Kernel

## Status

Accepted — 2026-05-29

## Context

SOTA layers (cross-core pipe, handle memory, gatekeeper, bus arbitrator, ECC, tokenizer)
were integrated incrementally but orchestration remained split between Arduino `loop()` and
ad-hoc Core 0 ingest. A unified kernel is required to document and enforce the dual-core
execution contract.

## Decision

### Feature 48 — M5Kernel

- `M5Kernel::start()` initializes the ring buffer, Core 0 protocol ingest, and Core 1
  application orchestration task.
- Core 1 loop drains the pipe, dispatches JSON/binary intents, runs supervisor compaction,
  telemetry, and hardware events.
- Registry-bearing JSON frames copy through virtual handles under gatekeeper supervision.
- Arduino `loop()` suspends indefinitely; processing is fully task-driven.
- Capability: `m5_central_kernel`.
- Telemetry: `kernel_processed_frames`, `kernel_orchestration_ticks`.

## Consequences

- `drainCorePipeFrames()` forwards to `m5KernelDrainPipeFrame()`.
- Architecture documented in `docs/en/architecture.md`.
- Host tests validate kernel constants via `kernel_runtime.py`.
