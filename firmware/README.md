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

Use PlatformIO in this folder:

```bash
pio run -t upload
```

## Protocol

See `schemas/intent.schema.json` and `schemas/telemetry.schema.json`.
