# Contributing

Thank you for improving Utah Flux Studio and the M5 Resolver platform.

## Product-first workflow

- **Users** should only need the GUI (`Start Utah Flux Studio.bat`).
- **Contributors** may use `make quality` and `pytest` for validation.

## Setup

```bash
cd host
pip install -e .
pip install pytest ruff mypy
```

## Common tasks

| Task | Location |
|------|----------|
| Add a Lego brick | `host/utah_flux/bricks.py` + `compiler.py` |
| Change Studio UI | `host/utah_flux/static/` |
| Intent / safety rules | `host/m5resolver/` |
| Firmware behavior | `firmware/src/` |
| Unit definitions | `registry/units.json` |
| User docs | `docs/en/`, `docs/zh/` |

## Quality checklist

- [ ] `pytest` passes
- [ ] New bricks have EN/ZH tutorial mention if user-facing
- [ ] Schema changes update `schemas/` and `schema-check` CI
- [ ] No requirement for end users to use CLI

## Docs

Update both English and Chinese docs when changing user-visible behavior.

## Pull requests

Use the PR template. Include screenshots of Utah Flux Studio for UI changes.
