# Omniscient Studio (Auto-Discovery Deck)

Lightweight **hardware discovery** UI without local LLM. Ideal when you only need to see Grove sensors appear on screen after plugging them in.

## Quick start

```text
pip install -e "host[daemon]"
```

Double-click **`launch/Start Omniscient Studio.bat`** or run:

```text
utah-flux-omniscient
```

Open **http://127.0.0.1:8000**.

## How it works

1. `HardwareMatrix` scans USB for Espressif VID `303A` (CoreS3 native USB).
2. Opens serial at 115200 baud.
3. Immortal Bootloader emits JSON discovery events on Grove Port A I2C scan.
4. WebSocket `/ws/telemetry` streams events to the browser deck.

## WebSocket events

| Payload | Meaning |
|---------|---------|
| `{"status":"IMMORTAL_KERNEL_LINKED","port":"COMx"}` | Device connected |
| `{"status":"AWAITING_HARDWARE"}` | No CoreS3 found |
| `{"event":"discovery","unit":"ENV_III_SENSOR",...}` | Sensor plugged in |
| `{"event":"disconnect",...}` | Sensor removed |

## UtahClaw vs Omniscient

| Feature | Omniscient (`:8000`) | UtahClaw (`:8024`) |
|---------|----------------------|---------------------|
| Auto USB scan | Yes | Yes |
| I2C discovery deck | Yes | Yes |
| Vibe-coding / Ollama | No | Yes |
| Auto-heal on errors | No | Yes |
| Canvas UI | `omniscient.html` | `utah_studio.html` |

Use **Omniscient** for classroom sensor demos. Use **UtahClaw** for full intent-resolution workflows.

## Related

- [UtahClaw Studio](utah-claw-studio.md)
- ADR [0044](../adr/0044-immortal-bootloader-autonomic-discovery.md)
