# Firmware

Universal M5Stack firmware terminal that:

- receives newline-delimited JSON intents over serial
- applies supported hardware actions (`display`, `speaker`, `power`)
- emits telemetry frames at fixed cadence
- returns structured ACK messages

## Build and flash

```bash
pio run -t upload
```

## Monitor

```bash
pio device monitor
```

## Contract notes

- Protocol transport: serial 115200 baud
- Input: line-delimited JSON
- Output:
  - telemetry: `{"type":"telemetry", ...}`
  - ack: `{"type":"ack","ok":true|false,...}`
