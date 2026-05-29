# ADR 0038: Android Asymmetric Gossip Mesh Participant (m5-android-mesh)

## Status

Accepted — 2026-05-29

## Context

ADR 0026 introduced Android USB binwire transport and basic UDP gossip. Mobile companions
needed full mesh participation: local registry mirror, gossip-driven preflight audit, and
automatic routing of validated `##` frames over USB Host without a desktop orchestrator.

## Decision

### Android

- `MeshRegistryMirror` — in-memory units mirror with SHA-256 fingerprint
- Enhanced `FluxwireMeshNode` — `registry_gossip` + `gossip_heartbeat` aligned with host mesh
- `AndroidMeshParticipant` — gossip → `MeshPreflightAudit` → `FastPathUsbBridge.dispatchRawFrame()`
- Existing `FastPathUsbBridge` / `WireFrames.kt` unchanged (10-byte big-endian `##`)

### Host

- `android_mesh.py` — `audit_android_mesh_registry()`, `compile_gossip_binwire_frame()`
- `test_android_mesh_gossip_preflight_and_binwire` complements `test_android_payload_binary_signature`

### Firmware

- Unchanged Core 0 CrossCorePipe `##` demux (no main.cpp task rewrite)

## Consequences

- Capability: `android_gossip_mesh_participant`
- Completes cross-platform loop: mesh → mobile audit → USB → dual-core firmware
