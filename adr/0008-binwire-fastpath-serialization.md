# ADR 0008: Binary Fast-Path Intent Serialization (m5-binwire)

## Status

Accepted — 2026-05-29

## Context

JSON intent parsing on ESP32 consumes CPU cycles and heap in deep FreeRTOS loops. Host-side
validation already guarantees schema safety; the wire transport can use a lean binary format
for hot mutations without sacrificing declarative JSON contracts at the composition layer.

## Decision

### Feature 12 — BinwireEncoder (host)

- Add `host/m5resolver/binwire.py` with magic header `##` and packed `!BBHI` payload.
- `encode_intent()` extracts fields from explicit `binwire` blocks or registry unit maps.
- CLI `--fastpath` validates JSON then sends binary via `IntentController.send_fastpath()`.

### Feature 13 — BinwireDecoder (firmware)

- Intercept serial stream when peek byte is `0x23`; bypass `ArduinoJson` on match.
- Zero-copy read into `BinwireCommand` packed struct with `ntohs` / `ntohl`.
- Apply GPIO + `StateForker` unit mutation through `registryApplyBinwireUnit()`.

### Feature 14 — Contract tests

- `tests/test_binwire.py` asserts header, alignment, and round-trip integrity.
- `tests/test_fluxwire.py` confirms binary frames coexist with flux graph JSON patches.

## Consequences

- Hybrid transport: JSON for human/config paths, binwire for sub-millisecond mutations.
- Binary frames are exactly 10 bytes; callers must not append newline terminators.
- Unit IDs are numeric (0–255); host maps registry keys via optional `unit_id_num`.

## References

- ADR 0002 Thin Firmware Boundary
- ADR 0007 Zero-Downtime State Forking
- `host/m5resolver/binwire.py`
- `firmware/src/BinwireDecoder.h`
