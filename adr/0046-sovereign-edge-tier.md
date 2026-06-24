# ADR 0046: Sovereign Edge Tier

## Status

Accepted — 2026-05-29

## Context

Edge devices need declarative phonon masking, cache-bounded telematic inference, and out-of-band execution frame mirroring without duplicating ESP-NOW radio initialization or replacing the integrated m5-kernel boot path.

## Decision

Add three modules under `SovereignEdge` coordinator:

1. **AcousticMask** — optional Core 0 I2S Brownian DMA task; degrades if pins/driver unavailable
2. **MatrixCompute** — IRAM 2-bit lattice `evaluateTelematicVector()`
3. **SwarmSoul** — packed `ExecutionFrame` over shared ESP-NOW bus (demux with `MeshStateVector`)

`sovereignEdgeInit()` after `omegaDefenseInit()` in `m5IntegratedKernelBoot()`.  
`sovereignEdgeTick()` at end of `omegaDefenseTick()`.

## Consequences

- New `sovereign_*` telemetry and three capability strings
- SwarmSoul receive path multiplexed in `MeshStateMirror` ESP-NOW callback
- Acoustic mask may be inactive on CoreS3 — acceptable degradation

## Related

- `firmware/src/SovereignEdge.*`
- `docs/en/sovereign-edge-tier.md`
