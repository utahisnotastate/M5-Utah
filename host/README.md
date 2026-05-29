# Host Packages

This folder contains two Python packages installed together:

## utah-flux (primary — users)

Visual Lego IDE for M5Stack. **Users never need the CLI.**

- Launch: double-click `Start Utah Flux Studio.bat` (repo root)
- Package: `utah_flux/`
- Entry: `utah-flux-studio`

## m5resolver (engine — developers)

Intent validation, safety, simulation, agent, registry operations.

- Used internally by Utah-Flux compiler and Studio API
- Optional for automation: `examples/agent_loop.py`

## Install (one time)

```bash
pip install -e .
```

Or double-click `Install Utah Flux.bat` at repo root.

## Tests

From repository root:

```bash
pytest
```
