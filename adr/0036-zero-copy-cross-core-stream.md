# ADR 0036: Zero-Copy Cross-Core Stream Piping

## Status

Accepted — 2026-05-29

## Context

ADR 0023 established the dual-core harness with `CrossCorePipe` (8192-byte NOSPLIT ring).
Host payloads still needed a compact fixed-width binary alias for streaming unit mode
changes without JSON duplication on the wire.

## Decision

### Host — `HostStreamPacker`

- Wire magic: `#S` (`0x23 0x53`), 6-byte fixed frame (`!BBH`)
- `IntentController.send_stream_frame()` and orchestrator `synchronize_stream_frame()`

### Firmware

- Reuses existing Core 0 `protocolCoreIngestTask` + `CrossCorePipe` ring (no main.cpp task rewrite)
- `StreamIntentDecoder` on Core 1 applies stream intents via `registryApplyBinwireUnit()`
- Demux order: `#M` → `#I` → `#R` → `#S` → `#P` → `#D` → `#F` → `##`

## Consequences

- Capability: `zero_copy_cross_core_stream`
- Test: `test_stream_payload_binary_signature_contracts`
- Complements `StreamRelayEncoder` JSON/binary ring wrappers
