# Omega Defense Stack (Tier-1 Edge Resiliency)

Firmware modules that harden M5Stack CoreS3 devices against timing side-channels, single-node failure, and forensic firmware extraction. Integrated via `omegaDefenseInit()` and `omegaDefenseTick()` in `firmware/src/OmegaDefense.cpp`.

## Modules

| Module | File(s) | Role |
|--------|---------|------|
| **Brownian Shield** | `StochasticShield.*` | Thermodynamic clock jitter (ADC + TRNG) around registry JSON dispatch |
| **Swarm Soul** | `MeshStateMirror.*` | ESP-NOW Byzantine state vectors every 10ms; ECC checksum; DeepSleep handoff |
| **Amnesia Kernel** | `AmnesiaKernel.*` | Volatile PSRAM payload vault; entropy scrub; IMU geographic anchor |
| **Chrono Scheduler** | `ChronoScheduler.*` | 100µs hyper-tick speculative task commits (motion → delayed alert) |
| **Tensor-Void Linkage** | `TensorVoidLinkage.*` | IRAM 2-bit quantized latent scoring on IMU vector |
| **Lazarus Daemon** | `LazarusDaemon.*` | RTC fast-memory boot counter + resurrection after panic/WDT |

## Boot integration

```
m5IntegratedKernelBoot()
  └── omegaDefenseInit()
        ├── stochasticShieldInit()
        ├── lazarusDaemonInit()
        ├── amnesiaKernelInit()
        ├── meshStateMirrorInit()
        └── chronoSchedulerInit()

M5Kernel applicationCoreLoop (Core 1)
  └── omegaDefenseTick(tick, frames)
        ├── heap anomaly → mesh suicide handoff
        ├── IMU → amnesia geographic anchor
        ├── mesh broadcast (10ms)
        └── tensor latent score
```

Registry JSON dispatch on Core 1 is wrapped in `StochasticShield::executeWithBrownianJitter`.

## Telemetry (`omega_*` metrics)

| Field | Meaning |
|-------|---------|
| `omega_tensor_score` | Last IRAM latent vector score |
| `omega_chrono_commits` | Speculative tasks committed |
| `omega_mesh_peer_updates` | Valid peer state vectors received |
| `omega_mesh_suicide_handoffs` | DeepSleep handoffs triggered |
| `omega_lazarus_boot_count` | RTC-persisted boot counter |
| `omega_amnesia_payload_bytes` | Bytes in volatile vault |

Query capabilities with `{"capability_query": true}` — includes `stochastic_execution_obfuscation`, `mesh_state_mirror`, `amnesia_ephemeral_vault`, `chrono_predictive_scheduler`, `tensor_void_linkage`, `lazarus_rtc_resurrection`.

## Ephemeral intent vault

Store mission parameters in volatile RAM only (never flash):

```json
{
  "ephemeral_store": true,
  "ephemeral": { "mission": "sanctum_alpha", "params": { "threshold": 0.8 } }
}
```

On IMU tamper or geographic drift, the Amnesia kernel entropy-scrubs PSRAM and restarts.

## Mesh failover (multi-device)

1. Flash two or more CoreS3 units with the same firmware.
2. ESP-NOW broadcasts state vectors every 10ms on channel 0.
3. Peer vectors with valid ECC checksum and higher `orchestration_tick` are adopted.
4. On critical heap pressure, primary broadcasts final state and enters DeepSleep; peer resumes.

## Design notes

- **No arbitrary code execution from PSRAM** — the Amnesia vault stores intent payloads for the existing JSON pipeline, not cast-and-call blobs (unsafe on embedded targets).
- **ESP-NOW degrades gracefully** — if radio init fails, single-node execution continues.
- **Lazarus** tracks resurrection via `esp_reset_reason()` + RTC flags, not fragile watchpoints.

## Related

- [firmware/README.md](../../firmware/README.md)
- [Architecture](architecture.md)
- ADR [0045](../adr/0045-omega-defense-edge-stack.md)
