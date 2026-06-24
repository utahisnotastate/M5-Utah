# UtahClaw Omniscient Studio — Intent-Resolution Canvas

**File:** `host/utah_flux/static/utah_studio.html` (also `utah_studio.html` at repo root)

## Launch

| Method | Command |
|--------|---------|
| One-time install | `Install UtahClaw.bat` |
| Windows launcher | `Start UtahClaw Studio.bat` (root) or `launch/Start UtahClaw Studio.bat` |
| CLI | `utah-claw-studio` or `py -m utah_flux.utahclaw_daemon` → http://127.0.0.1:8024 |
| Standalone HTML | Run daemon first, then open `utah_studio.html` |

## Requirements

- `pip install -e "host[claw]"`
- Ollama with `llama3` model
- M5Stack CoreS3 with Immortal Bootloader firmware (flash once)

See [utah-claw-studio.md](utah-claw-studio.md) for full guide (English) or [../zh/utah-claw-studio.md](../zh/utah-claw-studio.md) (中文).
