# ADR 0021: Resource-Aware Orchestration and Context-Aware Staging

## Status

Accepted — 2026-05-29

## Context

With JIT hot-loading, ECC repair, consensus routing, and dual-core piping active simultaneously,
ESP32 workloads can spike into heap and bus pressure. Without a coordinating layer, non-critical
intents compete with registry mutations and binary fast-paths during recovery.

## Decision

### Feature 49 — ResourceOrchestrator (firmware)

- Pressure levels: Nominal, Elevated, Critical based on free heap, handle pool utilization, bus rejects.
- Each M5Kernel orchestration tick calls `orchestrateTick()`.
- Critical pressure defers non-critical JSON (display/speaker/power); registry, JIT, compact, and binary frames proceed.
- Triggers handle-pool compaction under critical load.
- Telemetry: `orchestrator_pressure_level`, `orchestrator_deferred_frames`.

### Host mirror — HostResourceOrchestrator

- Evaluates device telemetry pressure before `send_intent()`.
- Defers non-critical host transmits when firmware reports critical pressure.

## Consequences

- Capability: `resource_aware_orchestrator`.
- Complements Feature 48 M5Kernel without replacing frame parsing on Core 0.
- Deferred intents receive `orchestrator_deferred_*` ack errors for host retry.
