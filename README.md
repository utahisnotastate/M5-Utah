# Utah Flux Studio

[![CI](https://github.com/utahisnotastate/M5-Utah/actions/workflows/ci.yml/badge.svg)](https://github.com/utahisnotastate/M5-Utah/actions/workflows/ci.yml)

**Build M5Stack projects like Lego — no command line, no coding required.**

Utah Flux Studio is a visual IDE for children, makers, and teams. Drag colorful bricks, connect them with wires, press **Play**, and your device runs the project.

## Start the app (no CLI)

### Windows (easiest)

Double-click:

`Start Utah Flux Studio.bat`

### After one-time setup

If Python is installed, run once from any file explorer / installer helper:

```text
pip install -e host
```

Then always use the double-click launcher above.

The studio opens in your browser at `http://127.0.0.1:8765`.

## How it works

1. **Drag bricks** from the left palette onto the board.
2. **Connect dots** — output dot → input dot (like Lego studs).
3. **Connect device** — USB cable + **Connect Device** (Chrome/Edge).
4. **Press Play** — Utah Flux compiles your project to safe device intents.

Under the hood:

- **Utah-Flux** library (`host/utah_flux/`) — Lego bricks, project files, compiler
- **m5resolver** engine (`host/m5resolver/`) — validation, safety, agentic recovery
- **Firmware** (`firmware/`) — runs intents on the M5Stack (flash once)

## One-time firmware flash (adult helper)

An adult only needs to flash firmware **once**:

```text
Open PlatformIO in the firmware folder and upload.
```

After that, children use only Utah Flux Studio.

## Project files

- Save: **Save Project** → `.flux.json` file
- Open: **Open Project** → pick your file
- Starters: built-in templates (Hello, Tilt Alarm, Party Mode)

## Repository layout

| Folder | Purpose |
|--------|---------|
| `host/utah_flux/` | Utah-Flux visual library + Studio server |
| `host/m5resolver/` | Intent engine, safety, agent (internal) |
| `firmware/` | Device runtime |
| `registry/` | Hardware unit catalog |
| `projects/` | Example `.flux.json` projects |
| `launch/` | Double-click launchers |
| `docs/` | Guides (English / 中文) |

## Documentation

| Language | Index |
|----------|--------|
| English | [docs/en/README.md](docs/en/README.md) |
| 中文 | [docs/zh/README.md](docs/zh/README.md) |

Tutorials for children, teachers, developers, engineers, and M5Stack staff are in `docs/*/tutorials/`.

Online docs: enable GitHub Pages from the `docs` workflow, or read Markdown in the repo.

## For developers

Optional: `pytest`, `make quality`, `host/m5resolver/` APIs, `examples/` scripts.  
**Not required for end users.**

## License

MIT — see `LICENSE`.
