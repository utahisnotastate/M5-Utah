# Firmware

Universal M5Stack runtime for **Utah Flux Studio**.

## What it does

- Receives JSON intents over USB serial (115200)
- Executes `display`, `speaker`, `power`
- Hot-reloads `registry` unit configurations
- Answers `capability_query`
- Emits telemetry (~20 Hz) with heap and IMU data
- Runs per-unit FreeRTOS workers with semantic actions (`registry_runtime.cpp`)

## User experience

End users **do not flash firmware themselves** after initial setup. An adult flashes once; children use only Utah Flux Studio.

## Flash once (adult / developer)

Use PlatformIO in this folder. **Close Ghost Forge** and any serial monitor first.

```bash
cd firmware
py -m platformio run -e m5stack-cores3 -t upload --upload-port COM4
```

Windows helper (same thing):

```powershell
cd firmware
.\flash-cores3.ps1
```

### CoreS3 upload fails with "No serial data received"

The board may be crash-looping on old firmware, or USB-CDC did not reset into the bootloader.

1. Unplug USB, close every app using the COM port.
2. Plug USB back in.
3. **Hold the LEFT button** on the CoreS3, **tap the side RESET once**, release RESET, release LEFT.
4. Within ~10 seconds, run upload again (slower 460800 baud is configured in `platformio.ini`).

After a good flash, serial boot should show `[M5-KERNEL]` and `[PIPE]` **without** `stack overflow in task speculative_sha`.

## Protocol

See `schemas/intent.schema.json` and `schemas/telemetry.schema.json`.

## Omega defense stack (Tier-1 edge resiliency)

Boot integrates six modules via `omegaDefenseInit()` in `M5IntegratedKernel.cpp`:

| Module | Role |
|--------|------|
| `StochasticShield` | ADC + TRNG thermodynamic jitter around registry JSON dispatch |
| `MeshStateMirror` | ESP-NOW Byzantine vectors (10ms), ECC checksum, DeepSleep handoff |
| `AmnesiaKernel` | Volatile PSRAM vault, entropy scrub wipe, IMU geo-anchor |
| `ChronoScheduler` | 100µs hyper-tick speculative task commits |
| `TensorVoidLinkage` | IRAM 2-bit quantized latent scoring |
| `LazarusDaemon` | RTC fast-memory resurrection telemetry |

Telemetry exposes `omega_*` metrics. Capability query includes `stochastic_execution_obfuscation`, `mesh_state_mirror`, `amnesia_ephemeral_vault`, `chrono_predictive_scheduler`, `tensor_void_linkage`, and `lazarus_rtc_resurrection`.

Optional intent flag `ephemeral_store: true` with an `ephemeral` field stores bytes in the Amnesia vault (never written to flash).
