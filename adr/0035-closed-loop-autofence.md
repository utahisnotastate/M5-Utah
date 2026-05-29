# ADR 0035: Closed-Loop Telemetry Autofence (m5-autofence)

## Status

Accepted — 2026-05-29

## Context

ADR 0024 introduced JSON `[TELEMETRY_STREAM]:` monitoring with binwire `##` remediation.
Edge deployments also need compact binary vitals uplink and `#R` downlink throttles for
sub-millisecond closed-loop healing without debugger attachment.

## Decision

### Host — `AutonomousRemediationEngine`

- Uplink: `[HEALTH_VITALS_STREAM]:` + hex-encoded `!BIB` diagnostic frame (1 Hz)
- Downlink: `#R` (`0x23 0x52`) remediation token `!BBH` (unit, safety pin, frequency)
- Wired through `IntentController.read_frame()` and `_process_frame()`
- Complements existing `AutonomousMitigationEngine` (binwire fallback when `#R` not emitted)

### Firmware

- `SystemHealthHarvester` on Core 1 — real heap + orchestration jitter metrics
- `RemediationDecoder` applies throttle via `registryApplyBinwireUnit()`
- Core 0 CrossCorePipe demux for fixed 6-byte `#R` frames

## Consequences

- Capability: `closed_loop_autofence`
- Test: `test_closed_loop_remediation_packing_contracts`
- Hex vitals encoding preserves line-oriented Fluxwire read loop
