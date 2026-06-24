# Reality Substrate (Class-1 Omega)

Firmware modules that dominate physical memory and kinetic matter: RF-kinetic mesh storage, zero-math robotics, ambient IoT compute, phyto-computing, spatial UI, causal debugging, eigen-state compilation, and genesis boot anchoring.

Coordinated by `RealitySubstrate` — `realitySubstrateInit()` after `sovereignEdgeInit()`; `realitySubstrateTick()` from `sovereignEdgeTick()`.

## Modules (Disclosures 7–14)

| Module | Role |
|--------|------|
| **AkashicFileSystem** | Fragment files into ESP-NOW RF flight; standing-wave rebroadcast (no SD/flash) |
| **ChronoKinetic** | Golden-ratio PWM servo relaxation (no PID) |
| **MnemonicProxy** | Promiscuous WiFi hive scan + ambient ESP-NOW tensor dispatch |
| **BiosymmetricBus** | DAC/ADC organic activation (phyto-computing substrate) |
| **SpatialUI** | Backlight-off magnetic flux projection (intent-gated) |
| **CausalDebugger** | setjmp probability shield; avoided-crash telemetry |
| **EigenStateCompiler** | Flux intent collapse into ephemeral vault |
| **GenesisProtocol** | RTC generation anchor on power-on boot |

## Intent API

```json
{"akashic_inject": true, "akashic_file_id": 42, "akashic": "mission payload"}
{"eigen_collapse": true, "flux_intent": "{...}"}
{"spatial_ui": true}
{"chrono_kinetic": {"target": 45.0}}
```

Ephemeral vault also accepts `ephemeral_store: true` (Omega Amnesia kernel).

## Telemetry (`substrate_*`)

| Field | Meaning |
|-------|---------|
| `substrate_akashic_fragments` | RF fragments held in RAM |
| `substrate_akashic_rebroadcasts` | Standing-wave re-energize count |
| `substrate_mnemonic_nodes` | Ambient nodes seen in hive scan |
| `substrate_mnemonic_dispatches` | Parasitic compute tasks sent |
| `substrate_biosymmetric_active` | Phyto bus available |
| `substrate_spatial_frames` | Magnetic projection frames |
| `substrate_causal_avoided` | Crashes avoided by causal shield |
| `substrate_eigen_collapses` | Intent collapse count |
| `substrate_genesis_generation` | RTC boot generation |
| `substrate_chrono_pwm` | Last chrono-kinetic PWM duty |

## ESP-NOW mesh demux

Shared bus (via `MeshStateMirror` init):

| Packet | Handler |
|--------|---------|
| `0xAF` magic | `AkashicFileSystem::RfFragment` |
| `0x4D` magic | `MnemonicProxy::ParasiticPayload` (outbound) |
| `sizeof(ExecutionFrame)` | `SwarmSoul` |
| `sizeof(MeshStateVector)` | `MeshStateMirror` |

## Design notes

- **No std::vector** — fixed fragment pools for embedded safety
- **SpatialUI** dims backlight only when `spatial_ui: true` intent is sent
- **GenesisProtocol** records RTC generation — does not bypass FreeRTOS or bootloader
- **MnemonicProxy** scans locally; does not attack third-party devices

## Related

- [Sovereign edge tier](sovereign-edge-tier.md)
- [Omega defense stack](omega-defense-stack.md)
- ADR [0047](../adr/0047-reality-substrate-class1.md)
