# Sovereign Edge Tier (Declarative Runtime)

Firmware modules that shift CoreS3 from static clock-cycle execution into an adaptive sovereign runtime: phonon-routing acoustic masking, IRAM matrix telematics, and asynchronous swarm conslation over the shared ESP-NOW bus.

Integrated via `sovereignEdgeInit()` and `sovereignEdgeTick()` (called from `omegaDefenseTick` on Core 1).

## Modules

| Module | File(s) | Role |
|--------|---------|------|
| **AcousticMask** | `AcousticMask.*` | I2S DMA Brownian noise stream on Core 0 (`mask_phonon` task) |
| **MatrixCompute** | `MatrixCompute.*` | IRAM 2-bit weight lattice telematic vector scoring |
| **SwarmSoul** | `SwarmSoul.*` | `ExecutionFrame` ESP-NOW conslation (10ms, shared mesh radio) |

## Boot integration

```
m5IntegratedKernelBoot()
  └── omegaDefenseInit()
  └── sovereignEdgeInit()
        ├── swarmSoulInit()
        └── acousticMaskInit()  → Core 0 phonon task if I2S available
```

Each orchestration tick:

```
omegaDefenseTick()
  └── sovereignEdgeTick()
        ├── MatrixCompute::evaluateTelematicVector(IMU + tick)
        └── SwarmSoul::serializeCurrentState()  (10ms, when mesh active)
```

ESP-NOW receive demux in `MeshStateMirror`:

- `sizeof(MeshStateVector)` → Byzantine mirror failover
- `sizeof(ExecutionFrame)` → SwarmSoul peer adoption

## Telemetry (`sovereign_*` metrics)

| Field | Meaning |
|-------|---------|
| `sovereign_matrix_score` | Last `MatrixCompute` telematic score |
| `sovereign_swarm_adoptions` | SwarmSoul peer frame adoptions |
| `sovereign_phonon_frames` | I2S DMA frames written |
| `sovereign_phonon_active` | `1` if acoustic mask task running |

Capabilities: `declarative_phonon_routing`, `memristive_matrix_compute`, `swarm_soul_conslation`.

## Platform notes

- **AcousticMask** uses legacy `driver/i2s.h` when available. On CoreS3 with M5 codec routing, I2S on GPIO 12/13/14 may be unavailable — the mask degrades gracefully with a serial log (no crash).
- **SwarmSoul** does not double-initialize ESP-NOW; it shares the mesh bus initialized by `MeshStateMirror`.
- **MatrixCompute** complements `TensorVoidLinkage` (3-axis IMU latent) with a 4+ dimension telematic lattice.

## Related

- [Omega defense stack](omega-defense-stack.md)
- [firmware/README.md](../../firmware/README.md)
- ADR [0046](../adr/0046-sovereign-edge-tier.md)
