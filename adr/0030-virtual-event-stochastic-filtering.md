# ADR 0030: Virtual Event Piping and Stochastic Resonance Filtering

## Status

Accepted — 2026-05-29

## Context

ADR 0007 introduced virtual event piping on the host. Firmware already emitted
`hardware_event` JSON from Core 1 and applied 1D Kalman filtering in telemetry.
This ADR completes the **Virtual Event Pipe Grid** with a dedicated transport prefix
and IMU-tuned stochastic filtering without replacing the dual-core harness.

## Decision

### Host

- `VirtualEventRouter.ingest_mesh_signal()` — alias for mesh / serial packet ingest
- `VIRTUAL_EVENT_STREAM_PREFIX` (`[VIRTUAL_EVENT_STREAM]:`) parsed in `IntentController.read_frame()`
- `parse_event_line()` strips prefix before JSON decode
- Default route `imu_tilt_event` → display intent patch

### Firmware

- `VirtualEventGrid.cpp` — `StochasticTelemetryFilter` (alias of `TelemetryKalmanFilter`, Q=0.015, R=0.550)
- `broadcastPristineEvent()` — static JSON on Fluxwire with virtual stream prefix
- `scanFilteredImuVirtualEvents()` — Core 1 IMU scan with rate limit; emits `imu_tilt_event` + `motion_spike_event`
- No changes to Core 0 serial demux or `vApplicationEngineTask` replacement

## Consequences

- Capability: `virtual_event_stochastic_filtering`
- Tests: `test_virtual_event_multiplexing_integrity` in `test_fluxwire.py`
- Host and firmware remain decoupled via registry-driven event_type strings
