# Compatibility Matrix

## Utah Flux Studio

| Feature | Status |
|---------|--------|
| Visual brick IDE | ✅ Shipping |
| WebSerial Play/Stop | ✅ Chrome, Edge |
| Save/Open `.flux.json` | ✅ |
| Starter templates | ✅ 4 built-in |

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

## Browser support

| Browser | WebSerial | Recommended |
|---------|-----------|-------------|
| Chrome | ✅ | Yes |
| Edge | ✅ | Yes |
| Firefox | ❌ | Use Chrome for connect |
| Safari | ❌ | Use Chrome for connect |
