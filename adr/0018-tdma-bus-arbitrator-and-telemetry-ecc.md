# ADR 0018: TDMA Bus Arbitration and Telemetry Hamming ECC

## Status

Accepted — 2026-05-29

## Context

Multi-unit I2C/SPI hot-swap topologies suffer bus contention and cross-talk when FreeRTOS
tasks access shared lines concurrently. Serial telemetry is also vulnerable to single-bit
corruption over long USB/serial runs, causing host agents to misread device state.

## Decision

### Feature 42 — BusArbitrator (firmware)

- TDMA slot table (8 units) with configurable `bus_arbitration_window_ms` per registry unit.
- Mutex-guarded `executeSafeBusTransaction()` wraps I2C/SPI hot-swap in `DynamicMultiplexer`.
- Transactions outside the time window are buffered/rejected with metrics.

### Feature 43 — TelemetryECC (firmware + host)

- Hamming (7,4) nibble encoding in firmware telemetry `ecc` block.
- `TelemetryECC.repair_telemetry_payload()` on host before fluxwire patch resolution.
- `IntentController.read_frame()` applies ECC repair on inbound telemetry frames.

### Feature 44 — Error injection tests

- `tests/test_ecc_codec.py` and fluxwire ECC integration tests.
- Bus arbitration window validation in `bus_validation.py`.

## Consequences

- Capabilities: `tdma_bus_arbitrator`, `telemetry_hamming_ecc`.
- Registry units may declare `bus_arbitration_window_ms` (5–60000 ms).
- Telemetry schema extended with optional `ecc` object and bus metrics.
