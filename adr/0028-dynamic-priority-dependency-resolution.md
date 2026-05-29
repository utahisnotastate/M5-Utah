# ADR 0028: Dynamic Priority Dependency Resolution

## Status

Accepted — 2026-05-29

## Context

Host agents updating `registry/units.json` must not deploy pin or bus contention that causes
priority inversion on firmware FreeRTOS tasks. Feature 58 adds predictive scheduling audit at
the test boundary before serial/wireless transmit.

## Decision

### Feature 58 — HostSchedulerCompiler enhancements

- Pin contention matrix with `realtime_critical` escalation to tier 3
- Shared bus key analysis (`bus:address`)
- Reverse dependency tier propagation via `StateGraphEngine`
- `SchedulingAudit`, `predictive_scheduling_audit()`, `compile_with_audit()`
- `audit_registry_file()` for `registry/units.json` preflight
- `IntentController.send_intent()` logs audit escalations/warnings before transmit

### Feature 59 — Verification tests

- `test_predictive_priority_inheritance_contracts` in `tests/test_validation.py`
- `test_registry_scheduler_audit_on_units_json` in `tests/test_registry.py`

Firmware `PriorityGatekeeper` + `assigned_priority_tier` in registry runtime unchanged (ADR 0019).

## Consequences

- Scheduling audit runs automatically when `enable_scheduler_compilation=True`
- Non-critical pin overlap yields warnings, not hard errors
- Critical overlap elevates both units to tier 3 for gatekeeper mutex boost
