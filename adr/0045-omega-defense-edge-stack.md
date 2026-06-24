# ADR 0045: Omega Defense Edge Stack

## Status

Accepted — 2026-05-29

## Context

Edge M5Stack devices in high-interference or contested environments need defenses beyond static deterministic execution: timing obfuscation, mesh state continuity, and volatile-only sensitive payloads.

## Decision

Integrate six firmware modules under `OmegaDefense` coordinator:

1. **StochasticShield** — thermodynamic jitter (ADC + TRNG) on critical dispatch paths
2. **MeshStateMirror** — ESP-NOW 10ms state vectors with ECC checksum and DeepSleep handoff
3. **AmnesiaKernel** — PSRAM ephemeral vault with IMU tamper wipe (no execute-from-RAM)
4. **ChronoScheduler** — 100µs esp_timer speculative commits
5. **TensorVoidLinkage** — IRAM 2-bit quantized scoring
6. **LazarusDaemon** — RTC fast-memory resurrection telemetry

Boot: `omegaDefenseInit()` in `M5IntegratedKernel.cpp` before `M5Kernel::start()`.  
Tick: `omegaDefenseTick()` each Core 1 orchestration cycle.

## Consequences

- Telemetry adds `omega_*` metrics; capability query advertises six new strings
- `ephemeral_store: true` intent stores bytes in volatile RAM only
- ESP-NOW mesh is optional; single-node mode degrades gracefully
- Amnesia vault does not cast PSRAM to function pointers (security)

## Related

- `firmware/src/OmegaDefense.*`
- `docs/en/omega-defense-stack.md`
