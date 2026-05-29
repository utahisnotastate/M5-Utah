# ADR 0025: Asymmetric Remote Procedure Piping (RPP)

## Status

Accepted — 2026-05-29

## Context

Text-heavy JSON intents incur heap allocation and parsing latency on ESP32 nodes executing
real-time control loops. Feature 54–56 introduce a Direct-Execution Kernel path: fixed-width
`#P` frames with the same `!BBHI` wire layout as binwire (`##`) but distinct magic bytes.

## Decision

### Feature 54 — Host RPP compiler

- `host/m5resolver/rpp_compiler.py` — `HostRPPCompiler.compile_rpp_frame()`
- Magic `\x23\x50` (#P), 10-byte frames (2 + 8)
- Wired through `FastPathSerializer.try_encode()` and `IntentController.send_rpp()`

### Feature 55 — Micro-Execution Kernel (firmware)

- `RPPDecoder.h/cpp` — `MicroExecutionKernel` stack-local dispatch
- Core 0 `CrossCorePipe` demuxes `#P` before pushing to ring; Core 1 applies via `processInboundBinaryPayload`
- Opcodes: `0x01` pin HIGH, `0x02` pin LOW (extensible)

### Feature 56 — Contract tests

- `test_rpp_binary_payload_alignment_contracts` in `tests/test_fluxwire.py`

Note: Feature 53 remains telemetry self-healing (ADR 0024). RPP is numbered 54–56 in the SOTA index.

## Consequences

- Capability: `asymmetric_rpp_piping`
- Complements binwire (`##`) without replacing M5Kernel / resource orchestration
- Intent schema `rpp` block and `rpp_execute` vibe action supported
