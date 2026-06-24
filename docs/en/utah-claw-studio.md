# UtahClaw Omniscient Studio

The **Intent-Resolution Canvas** is a zero-dependency HTML interface that connects to your local UtahClaw daemon over WebSocket. No cloud APIs, no npm build step — just Chromium and loopback TCP.

## Quick start (recommended)

1. Install once (from repository root):
   ```text
   Install UtahClaw.bat
   ```
   Or manually: `pip install -e "./host[claw]"` (use repo root path on Windows).
2. Start Ollama: `ollama run llama3`
3. Flash Immortal Bootloader + Omega defense firmware once (see [firmware/README.md](../../firmware/README.md)).
4. Double-click **`Start UtahClaw Studio.bat`** at repo root (or `launch/Start UtahClaw Studio.bat`).
5. Browser opens **http://127.0.0.1:8024** — keep the **UtahClaw Daemon** console window open.

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `ERR_CONNECTION_REFUSED` on :8024 | Daemon not running — run `Install UtahClaw.bat`, then `Start UtahClaw Studio.bat`; check daemon window for `ModuleNotFoundError: fastapi` |
| Page loads but vibe fails | Start `ollama run llama3` in another terminal |
| `Linked: COMx` missing | Plug CoreS3 USB; close other serial monitors (only one app per COM port) |

## What you see

| Panel | Purpose |
|-------|---------|
| **Hardware deck** | Auto-detected Grove units from Immortal I2C discovery |
| **Silicon telemetry** | Raw serial lines from M5Stack |
| **UtahClaw console** | Local Llama-3 responses and auto-heal events |
| **Manifest** | Send plain-English intent → JSON/code → device |

## Standalone HTML file

`utah_studio.html` at the repository root can be opened directly, but the **UtahClaw daemon must be running** first:

```text
utah-claw-studio
```

Then double-click `utah_studio.html` or open http://127.0.0.1:8024.

When opened as a `file://` URL, the canvas defaults to `ws://127.0.0.1:8024/ws/studio`.

## WebSocket protocol

**Outbound (browser → daemon):**

```json
{"type": "vibe_request", "intent": "Make the screen red"}
```

**Inbound (daemon → browser):**

| `type` | Meaning |
|--------|---------|
| `log` | Serial telemetry line |
| `agent` | UtahClaw status or generated code |
| `discovery` | Grove sensor attach/detach (`data` object) |

## Auto-healing loop

When serial output matches error patterns (`Traceback`, `SyntaxError`, `Guru Meditation`, etc.), UtahClaw:

1. Notifies the agent panel
2. Sends the error to local Ollama
3. Pushes corrected JSON or MicroPython paste-mode to the device

## Privacy and monetization positioning

- **100% offline** — schematics and intents never leave the machine
- Suitable for **Sovereign Foundry** packaging (PyInstaller `.exe` + pre-flashed CoreS3 kits)
- Pro-tier positioning: privacy-focused hardware teams, STEM labs, air-gapped environments

## Related

- [Omniscient Studio](omniscient-studio.md) — discovery-only deck (no LLM)
- [Architecture](architecture.md) — Immortal Bootloader + dual-core kernel
- ADR [0044](../adr/0044-immortal-bootloader-autonomic-discovery.md)
