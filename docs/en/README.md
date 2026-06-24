# English Documentation

## Start here

**Utah Flux Studio** — double-click `Start Utah Flux Studio.bat` at the repository root.

## Guides

| Audience | Guide | Step-by-step tutorial |
|----------|-------|------------------------|
| Children | [children.md](children.md) | [tutorials/children-tutorial.md](tutorials/children-tutorial.md) |
| Parents / non-technical | [non-technical-users.md](non-technical-users.md) | [tutorials/non-technical-tutorial.md](tutorials/non-technical-tutorial.md) |
| Developers | [technical-users.md](technical-users.md) | [tutorials/technical-tutorial.md](tutorials/technical-tutorial.md) |
| Electronics engineers | [electronics-engineers.md](electronics-engineers.md) | [tutorials/engineers-tutorial.md](tutorials/engineers-tutorial.md) |
| M5Stack employees | [m5stack-employee-migration-playbook.md](m5stack-employee-migration-playbook.md) | [tutorials/employee-tutorial.md](tutorials/employee-tutorial.md) |

## Operations

- [operations-runbook.md](operations-runbook.md)
- [compatibility-matrix.md](compatibility-matrix.md)
- [github-governance-setup.md](github-governance-setup.md)

## Studios (v0.8+)

| Studio | Launcher | Guide |
|--------|----------|-------|
| Utah Flux Lego IDE | `Start Utah Flux Studio.bat` | — |
| Omniscient discovery deck | `launch/Start Omniscient Studio.bat` | [omniscient-studio.md](omniscient-studio.md) |
| UtahClaw intent canvas | `Start UtahClaw Studio.bat` | [utah-claw-studio.md](utah-claw-studio.md) · [intent-resolution-canvas.md](intent-resolution-canvas.md) |
| System architecture | — | [architecture.md](architecture.md) |
| Omega defense (firmware) | flash once | [omega-defense-stack.md](omega-defense-stack.md) |
| Field graph / Sanctum | `field_compiler.py` | [field-graph-compiler.md](field-graph-compiler.md) |

## Features (v0.8.2)

- Visual Lego brick IDE (no CLI for end users)
- **Immortal Bootloader** — flash firmware once, I2C auto-discovery forever
- **UtahClaw canvas** — offline Llama-3 vibe-coding + serial auto-heal
- **Omniscient deck** — driverless Espressif USB scan + live sensor cards
- **Omega defense stack** — jitter, mesh mirror, PSRAM vault, chrono/tensor/lazarus modules
- **Field graph compiler** — `nodes`/`bindings` sanctum projects → display intents
- Formal typestate enforcement and m5-secure anti-replay wire fences
- Real-time terminal state dashboard (`enable_dashboard=True`)
- Intent-first device control (`display`, `speaker`, `power`, `registry`)
- Safety validation, agentic remediation, HCP registry
- Starter templates and save/open `.flux.json` projects
