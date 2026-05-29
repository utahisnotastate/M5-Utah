# ADR 0010: Cryptographic Hardware Enclaves and Kalman Telemetry Filtering

## Status

Accepted — 2026-05-29

## Context

IoT deployments face firmware spoofing, unsigned intent injection, and noisy sensor telemetry
causing false-positive agent remediation loops. Industrial trust anchors require edge verification
before registry hot-reload and mathematically smoothed telemetry for host agents.

## Decision

### Feature 18 — CryptoEnclave (firmware)

- `CryptoEnclave` validates `security.signature_hex` via SHA-256 over canonical intent body.
- Failed verification blocks processing and emits `security_alarm` frames.
- Unsigned intents remain allowed in dev mode; optional `M5_REQUIRE_SIGNED_REGISTRY` compile flag.

### Feature 19 — TelemetryKalmanFilter (firmware)

- 1D Kalman filters per IMU axis in `TelemetryFilter.h`.
- Telemetry JSON exposes filtered `accel` plus raw `accel_raw` for audit.

### Feature 20 — Host security validation

- `host/m5resolver/security.py` signs and verifies intents with `sha256-canonical-v1`.
- `validate_intent_payload()` rejects tampered signatures; optional registry signature requirement.
- CLI `--sign` and `--require-registry-signature` flags.

## Consequences

- Host and firmware must use matching canonical key ordering for digest parity.
- Binwire fast-path frames bypass JSON signature envelope (pre-authorized binary channel).
- Full ATECC608A / ESP32-S3 DS peripheral integration is abstracted behind `CryptoEnclave`.

## References

- ADR 0008 Binwire Fast-Path Serialization
- `firmware/src/CryptoEnclave.h`
- `host/m5resolver/security.py`
