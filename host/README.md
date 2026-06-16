# Utah Flux Host Package (`utah-flux`)

Python host plane for **m5-utah** — install from this directory:

```text
pip install -e .
pip install -e ".[daemon]"   # Omniscient auto-discovery deck
pip install -e ".[claw]"       # UtahClaw + Ollama vibe-coding
```

## Entry points

| Command | Port | Description |
|---------|------|-------------|
| `utah-flux-studio` | 8765 | Lego brick IDE (children / makers) |
| `utah-flux-omniscient` | 8000 | Grove I2C auto-discovery WebSocket deck |
| `utah-claw-studio` | 8024 | Intent-Resolution Canvas + offline Llama-3 |
| `m5-vibe-server` | 8023 | WebUSB vibe gateway |

Windows launchers live in `../launch/` at the repository root.

## Packages

| Path | Role |
|------|------|
| `utah_flux/` | Visual compiler, studios, `utah_studio.html` canvas |
| `m5resolver/` | Intent engine, typestate, secure wire, mesh, agent |

## Quick test

```text
cd ..
py -m pytest tests/ -q
```

## Documentation

Full project docs: [../docs/en/README.md](../docs/en/README.md) · [../docs/zh/README.md](../docs/zh/README.md)

- [UtahClaw studio](../docs/en/utah-claw-studio.md)
- [Omniscient deck](../docs/en/omniscient-studio.md)
- [Architecture](../docs/en/architecture.md)

## Version

See `pyproject.toml` (currently **0.8.1**).
