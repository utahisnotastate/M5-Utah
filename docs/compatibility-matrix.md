# Compatibility Matrix / 兼容性矩阵

## Board Support / 板卡支持

| Board | Firmware Status | Telemetry | Intent Actions | Notes |
|---|---|---|---|---|
| CoreS3 | Primary target | accel, battery, charging | display, speaker, power | Fully supported by current PlatformIO config |
| Core2 (v1.1) | Planned profile | expected similar | expected similar | Add board profile in firmware pipeline |
| StickC Plus2 | Planned profile | partial (no touch) | display/speaker limited by model | Validate PMU and speaker capabilities |
| Cardputer | Planned profile | keyboard-focused telemetry TBD | display and tone TBD | Requires keyboard input contract |
| NanoC6 | Planned profile | minimal telemetry | intent subset | Low-power profile and transport tuning |

## Protocol Compatibility / 协议兼容性

| Contract | Version | Status | Breaking Changes |
|---|---|---|---|
| Intent schema | 0.1 | stable pre-1.0 | none |
| Telemetry schema | 0.1 | stable pre-1.0 | none |
| Serial framing | line-delimited JSON | stable | none |

## Migration Guidance / 迁移建议

- New features should target intent and registry contracts first.
- Legacy board-specific repositories should map into this matrix and be classified as bridge/reference/retired.
- Update this matrix for every board profile change and release.
