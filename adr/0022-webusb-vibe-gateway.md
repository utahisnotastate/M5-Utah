# ADR 0022: WebUSB Vibe Gateway and Compile Pipeline

## Status

Accepted — 2026-05-29

## Context

End-users need to plug an M5Stack or ESP32 over WebUSB/WebSerial and vibe-code reactive
applications without manual file parsing. The host already validates intents, compiles
binwire fast-path frames, and the firmware demuxes `##` tokens on Core 0 — but there was
no unified browser gateway tying natural language, schema validation, resource preflight,
and wire injection together.

## Decision

### Feature 50 — WebUSB Agentic Automation Server

- `host/m5resolver/vibe_server.py` — ThreadingHTTPServer broker on port 8023
- `host/m5resolver/vibe_pipeline.py` — compile → validate → resource preflight → binwire/JSON wire
- `host/m5resolver/static/vibe-ide.html` — WebSerial IDE with `/compile_vibe` octet-stream dispatch
- `IntentController.compile_vibe_for_wire()` — shared host orchestration hook
- Optional `--serial COMx` host bridge for server-side injection alongside browser WebSerial

### Feature 51 — Fast-path regression mapping

- `test_fast_path_binary_encoder_bounds` in `tests/test_fluxwire.py` — magic header and `!BBHI` contract
- `tests/test_vibe_server.py` — pipeline and HTTP endpoint integration tests

### Vibe compiler GPIO branch

- Prompts like "blink GPIO pin 10 at 50Hz" compile to `fast_track_gpio` intents with `fastpath: true`
- Pipeline routes through existing `FastPathSerializer` / firmware `BinwireDecoder` — no `main.cpp` loop regression

## Consequences

- Zero-install local gateway: `py -m m5resolver.vibe_server` or `m5-vibe-server`
- Browser pushes fixed-width binwire or JSON lines; firmware path unchanged (CrossCorePipe → M5Kernel)
- LLM hook point remains in `compile_vibe_to_intent()` for future provider integration
