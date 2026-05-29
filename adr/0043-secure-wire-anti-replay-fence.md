# ADR 0043: Hardware-Backed Secure Wire Anti-Replay Fences (m5-secure)

## Status

Accepted — 2026-05-29

## Context

Hot-swapped binary deltas over serial or Android mesh are vulnerable to MitM replay
if an adversary rebroadcasts captured motor-control or IRAM patch frames.

Full TLS on ESP32 adds latency and heap pressure. A lightweight monotonic sequence
fence validates frame freshness in microseconds on Core 0.

## Decision

### Wire format

- Magic: `#A` (`0x23 0x41`) — distinct from `#S` stream (`0x23 0x53`) per ADR 0036
- Payload: `!BBHI` (unit, opcode, data vector, monotonic sequence id)
- Frame length: 10 bytes fixed

### Host

- `host/m5resolver/secure_wire.py` — `SecureWireEncoder` with incrementing sequence pool
- `IntentController.send_fastpath()` wraps `##` / `#P` frames when `enable_secure_wire=True`

### Firmware

- `SecureWireFence` — Core 0 ingest in `CrossCorePipe.cpp` drops `sequence <= lastObserved`
- Emits `security_alarm` JSON on replay rejection via `emitSecurityAlarm()`
- Core 1 `SecureWireDecoder_processPayload()` applies attested mutations after ring delivery
- Does not replace CrossCorePipe / M5Kernel dual-core layout

### Tests

- `test_secure_monotonic_sequence_contracts` in `tests/test_validation.py`

## Consequences

- Stream `#S` frames remain 6-byte zero-copy piping unchanged
- Host and firmware must agree on `#A` magic (not legacy conceptual `##S` label)
- Sequence state resets on device reboot; host should bump baseline after reconnect
