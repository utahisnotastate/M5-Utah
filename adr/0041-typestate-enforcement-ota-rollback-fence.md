# ADR 0041: Formal Typestate Enforcement and OTA Rollback Fences

## Status

Accepted — 2026-05-29

## Context

Conversational intents can request individually valid actions that violate hardware
operational state sequences (e.g. hot-patching a peripheral mid-transaction). OTA
updates without double-buffered commit boundaries risk bricking devices on partial
transmissions.

## Decision

### Host — Typestate Enforcement

- `host/m5resolver/typestate.py` — `SystemTypestateEnforcer` with explicit
  `VALID_TRANSITIONS` directed graph
- `IntentController.send_intent()` calls `validate_intent_typestate()` before
  resource orchestration when `enable_typestate_enforcement=True` (default)
- Registry units with `target_state` are validated against `current_state`/`state`
- DAG cycle detection via existing `StateGraphEngine.validate_dag()`

### Firmware — OTA Rollback Fence

- `OtaRollbackFence.{h,cpp}` — passive partition allocation via `esp_ota_*`
- Wired from `m5IntegratedKernelBoot()` as `otaRollbackFenceInit()` after
  `registryRuntimeInit()` — does not alter dual-core CrossCorePipe / M5Kernel layout
- Gracefully dormant when no OTA partition table is configured

### Tests

- `tests/test_typestate.py` — legal/illegal transition contracts and intent blocking

## Consequences

- Illegal state transitions return preflight errors without hitting the wire
- OTA commit requires explicit `verifyAndCommitOtaState()` after staged writes
- Production dual-core pipeline remains unchanged
