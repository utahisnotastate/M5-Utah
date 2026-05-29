# ADR 0016: Cross-Core Ring Pipe and Zero-Copy Tokenizer

## Status

Accepted — 2026-05-29

## Context

Serial intent processing on a single core copies UART data through multiple parser layers,
introducing jitter under load. ESP32 dual-core hardware allows isolating protocol ingestion
from application execution when a lock-free queue bridges the cores.

## Decision

### Feature 36 — CrossCorePipe (firmware)

- FreeRTOS `RINGBUF_TYPE_NOSPLIT` ring (8192 bytes) bridges Core 0 ingest and Core 1 execution.
- Core 0 `ProtocolCore` task reads serial lines and complete binary frames, pushes typed pipe items.
- Core 1 `loop()` drains via `drainCorePipeFrames()` without blocking on UART IO.

### Feature 37 — InPlaceTokenizer (firmware)

- Non-JSON payloads tokenized in-place by overwriting `,` and `:` with `\0`.
- JSON payloads (`{` / `[` prefix) bypass tokenizer and use existing ArduinoJson path.

### Feature 38 — Stream relay validation (host)

- `StreamRelayEncoder` wraps JSON/binary payloads with pipe frame markers for alignment checks.
- `FluxGraph.validate_relay_patch()` verifies fluxwire patches fit ring slot boundaries.
- `IntentController.send_relay_intent()` pre-validates before JSON transmit.

### Safety fix — I2C bus frequency

- Registry units with `type: I2C` or `SPI` validate `frequency_hz` against 1 MHz bus limit,
  not the 60 Hz unit loop limit.

## Consequences

- Capabilities: `cross_core_ring_pipe`, `zero_copy_tokenizer`.
- Host wire format remains newline-delimited JSON and raw binary magics; pipe framing is internal
  to the ESP32 cross-core queue.
- Binary demux on Core 0 assembles full frames before enqueue to avoid partial ring items.
