# ADR 0026: Android Host Integration Layer

## Status

Accepted — 2026-05-29

## Context

Mobile developers need a plug-and-play path to drive M5Stack/ESP32 hardware without root or
custom kernel drivers. The Python host already participates in Fluxwire gossip as
`android_host_node`; the Android companion must emit the same fixed-width wire contracts as
`BinwireEncoder` and integrate as an active mesh peer.

## Decision

### Features 57–58 — Android USB Host transport bridge

- `android/src/.../transport/FastPathUsbBridge.kt` — USB Host bulk OUT, coroutine-scoped writes
- `WireFrames.kt` — Big-endian `##` binwire and `#P` RPP packers (10 bytes each)
- `FluxwireMeshNode.kt` — UDP gossip on port 23023 matching `FluxwireGossipMesh`
- `host/m5resolver/android_bridge.py` — Python contract mirror for CI
- `test_android_payload_binary_signature` in `tests/test_fluxwire.py`

Firmware ingestion unchanged: Core 0 CrossCorePipe demuxes `##` into `DirectHardwareCommand`.

## Consequences

- Capability: `android_usb_host_bridge`
- No firmware loop changes required — Android frames are wire-identical to host binwire
- Android module is source-drop (no Gradle wrapper in repo); embed in companion apps
