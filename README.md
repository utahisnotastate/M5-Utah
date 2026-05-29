# Utah Flux Studio / m5-utah

[![CI](https://github.com/utahisnotastate/M5-Utah/actions/workflows/ci.yml/badge.svg)](https://github.com/utahisnotastate/M5-Utah/actions/workflows/ci.yml)
[![m5utah CI](https://github.com/utahisnotastate/M5-Utah/actions/workflows/m5utah-ci.yml/badge.svg)](https://github.com/utahisnotastate/M5-Utah/actions/workflows/m5utah-ci.yml)

**Build M5Stack projects like Lego — no command line, no coding required.**

Utah Flux Studio is a visual IDE for children, makers, and enterprise teams. Drag colorful bricks, connect them with wires, press **Play**, and your device runs the project. Under the hood, **m5-utah** is a production-ready intent-first framework: dual-core FreeRTOS microkernel, zero-copy binary wire formats, formal typestate verification, and hardware-backed anti-replay fences.

## Start the app (no CLI)

### Windows (easiest)

Double-click:

`Start Utah Flux Studio.bat`

### After one-time setup

If Python is installed, run once:

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
- **m5resolver** engine (`host/m5resolver/`) — validation, typestate, secure wire, agentic recovery
- **Firmware** (`firmware/`) — dual-core M5Kernel runtime on ESP32 (flash once)

## Why m5-utah vs the alternatives

The M5Stack ecosystem offers many entry points. **m5-utah** is the only stack that combines a child-friendly visual IDE with an enterprise-grade intent pipeline, dual-core orchestration, and cryptographically sequenced fast-path wire transport.

| Capability | **m5-utah** | Arduino IDE + M5Unified | ESP-IDF (native) | UIFlow 2 | PlatformIO + Arduino | MicroPython (M5) | M5Stack EZData / Cloud |
|------------|:-----------:|:-----------------------:|:----------------:|:--------:|:--------------------:|:----------------:|:----------------------:|
| Zero-CLI visual IDE for children | ✅ | ❌ | ❌ | ✅ | ❌ | ❌ | Partial (cloud UI) |
| Intent-first / declarative control plane | ✅ | ❌ | ❌ | Blocks only | ❌ | ❌ | Data-only |
| Conversational vibe-coding gateway | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Dual-core protocol / app partitioning | ✅ | ❌ | Manual FreeRTOS | Opaque | Manual | ❌ | N/A |
| Zero-copy binary fast-path (`##`, `#P`, `#A`) | ✅ | ❌ | Custom | ❌ | Custom | ❌ | ❌ |
| Formal typestate transition enforcement | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Monotonic anti-replay secure wire (m5-secure) | ✅ | ❌ | Custom TLS/MBED | ❌ | Custom | ❌ | HTTPS only |
| OTA double-buffer rollback fence | ✅ | Partial (Arduino OTA lib) | ✅ (manual) | Opaque | Partial | ❌ | Cloud OTA |
| Real-time terminal state dashboard | ✅ | ❌ | Custom | ❌ | ❌ | ❌ | Web charts |
| Bitmapped structural delta compiler | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| IRAM vector fence / JIT overlays | ✅ | ❌ | Advanced manual | ❌ | Advanced manual | ❌ | ❌ |
| Closed-loop autofence remediation | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | Alerts only |
| Android mesh participant + USB bridge | ✅ | ❌ | Custom | ❌ | Custom | ❌ | Partial |
| Agentic telemetry recovery | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Hardware Context Protocol registry | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Time-travel / replay journal | ✅ | ❌ | Custom | ❌ | Custom | ❌ | ❌ |
| CI: host pytest + firmware PlatformIO matrix | ✅ | ❌ | Project-specific | ❌ | Project-specific | ❌ | ❌ |
| Schema-validated intent contracts | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Hamming ECC telemetry repair | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Open-source MIT, self-hostable | ✅ | ✅ | ✅ | ❌ (closed cloud) | ✅ | ✅ | ❌ |
| Learning curve for non-programmers | **Low** | High | Very high | Low | High | Medium | Low (data) |
| Bare-metal performance on ESP32 | **High** | Medium | **High** | Medium | Medium | Low | N/A |

**Summary:** Arduino and ESP-IDF give you raw control but no unified intent pipeline, no typestate guards, and no kid-friendly IDE. UIFlow and EZData optimize for beginners or cloud dashboards but hide the wire protocol and lack formal verification, anti-replay fences, and dual-core orchestration. **m5-utah** targets both audiences: Lego-simple UX up front, bulletproof engineering underneath.

## Production architecture (v0.7)

```
[Human intent / Utah Flux / vibe IDE]
              │
              ▼
[typestate.py] ──► mathematical state legality
              │
              ▼
[secure_wire.py] ──► monotonic sequence tokens (#A)
              │
              ▼  fluxwire binary transport
[Core 0 CrossCorePipe] ──► SecureWireFence drops replays
              │
              ▼  lock-free ring
[Core 1 M5Kernel] ──► registry, JIT, telemetry, autofence
```

See [docs/en/architecture.md](docs/en/architecture.md) and ADRs `0041`–`0043` for typestate, OTA rollback, dashboard, and secure wire details.

## One-time firmware flash (adult helper)

An adult only needs to flash firmware **once**:

```text
cd firmware
py -m platformio run -e m5stack-cores3 -t upload
```

After that, children use only Utah Flux Studio.

## Developer tooling

| Tool | Purpose |
|------|---------|
| `pytest tests/` | Host contract + validation suite (154+ tests) |
| `enable_dashboard=True` | Live terminal system matrix from health vitals |
| `enable_secure_wire=True` (default) | Anti-replay wrapping on `send_fastpath()` |
| `make quality` | Lint / type checks (optional) |

## Project files

- Save: **Save Project** → `.flux.json` file
- Open: **Open Project** → pick your file
- Starters: built-in templates (Hello, Tilt Alarm, Party Mode)

## Repository layout

| Folder | Purpose |
|--------|---------|
| `host/utah_flux/` | Utah-Flux visual library + Studio server |
| `host/m5resolver/` | Intent engine, typestate, secure wire, agent |
| `firmware/` | Dual-core device runtime |
| `registry/` | Hardware unit catalog |
| `android/` | Mesh participant + USB fast-path bridge |
| `projects/` | Example `.flux.json` projects |
| `launch/` | Double-click launchers |
| `adr/` | Architecture decision records |
| `docs/` | Guides (English / 中文) |

## Documentation

| Language | Index |
|----------|--------|
| English | [docs/en/README.md](docs/en/README.md) |
| 中文 | [docs/zh/README.md](docs/zh/README.md) |

Tutorials for children, teachers, developers, engineers, and M5Stack staff are in `docs/*/tutorials/`.

## License

MIT — see `LICENSE`.
