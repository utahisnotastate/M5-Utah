# Compatibility Matrix

## Utah Flux Studio

| Feature | Status |
|---------|--------|
| Visual brick IDE | ✅ Shipping |
| WebSerial Play/Stop | ✅ Chrome, Edge |
| Save/Open `.flux.json` | ✅ |
| Starter templates | ✅ 4 built-in |
| UtahClaw intent canvas | ✅ port 8024 |
| Omniscient discovery deck | ✅ port 8000 |
| Immortal I2C discovery firmware | ✅ CoreS3 |
| Omega defense stack | ✅ v0.8.2 |
| Sovereign edge tier | ✅ v0.8.3 |
| Field graph compiler (Sanctum) | ✅ `field_compiler.py` |
| `Install UtahClaw.bat` / root launcher | ✅ Windows |

## Boards

| Board | Firmware | Utah Flux | Notes |
|-------|----------|-----------|-------|
| CoreS3 | Primary | ✅ | Default `platformio.ini` target |
| Core2 v1.1 | Planned | 🔜 | Add env + profile |
| StickC Plus2 | Planned | 🔜 | Validate speaker/display |
| Cardputer | Planned | 🔜 | Keyboard bricks TBD |
| NanoC6 | Planned | 🔜 | Low-power profile |

## Protocol versions

| Contract | Version | Studio | Firmware |
|----------|---------|--------|----------|
| Intent schema | 0.1+ | compile gate | execute |
| Telemetry schema | 0.1+ | Live Log | emit |
| Registry (HCP) | 0.1 | merge on compile | hot-reload |
| Secure wire (#A) | 0.7+ | `SecureWireEncoder` | `SecureWireFence` |
| Immortal discovery | 0.8+ | `HardwareMatrix` | `ImmortalDiscovery` |
| Omega defense | 0.8.2+ | N/A | `OmegaDefense` + six modules |
| Ephemeral vault intent | 0.8.2+ | optional inject | `AmnesiaKernel` |
| Field graph compile | 0.8.2+ | `field_compiler.py` | display intents only |
| Typestate graph | 0.6.8+ | preflight | N/A (host) |

## Browser support

| Browser | WebSerial | Recommended |
|---------|-----------|-------------|
| Chrome | ✅ | Yes |
| Edge | ✅ | Yes |
| Firefox | ❌ | Use Chrome for connect |
| Safari | ❌ | Use Chrome for connect |
