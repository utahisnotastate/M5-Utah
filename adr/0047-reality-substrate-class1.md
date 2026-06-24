# ADR 0047: Reality Substrate (Class-1 Omega)

## Status

Accepted — 2026-05-29

## Context

Class-1 Omega architecture requires non-local mesh storage, kinetic actuation without PID, ambient compute offload, optional phyto/analog activation, spatial UI modes, causal crash avoidance, eigen intent collapse, and genesis boot telemetry — without replacing the integrated m5-kernel or using unbounded STL on ESP32.

## Decision

Add eight modules under `RealitySubstrate` coordinator (disclosures 7–14):

1. `AkashicFileSystem` — RF fragment standing wave on shared ESP-NOW
2. `ChronoKinetic` — golden-ratio PWM relaxation
3. `MnemonicProxy` — promiscuous scan + parasitic tensor dispatch
4. `BiosymmetricBus` — DAC/ADC organic activation when hardware allows
5. `SpatialUI` — intent-gated magnetic projection (backlight off)
6. `CausalDebugger` — setjmp execution shield
7. `EigenStateCompiler` — flux intent → Amnesia vault
8. `GenesisProtocol` — RTC generation anchor

Boot: `realitySubstrateInit()` after `sovereignEdgeInit()`.  
Tick: `realitySubstrateTick()` at end of `sovereignEdgeTick()`.

Mesh receive demux extended with magic-byte prefixes for Akashic fragments.

## Consequences

- New `substrate_*` telemetry and eight capability strings
- Intent keys: `akashic_inject`, `eigen_collapse`, `spatial_ui`, `chrono_kinetic`
- Spatial UI and mnemonic hive are opt-in / degraded gracefully on CoreS3

## Related

- `firmware/src/RealitySubstrate.*`
- `docs/en/reality-substrate.md`
