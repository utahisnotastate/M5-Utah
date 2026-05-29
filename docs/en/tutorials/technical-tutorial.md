# Technical Tutorial — Utah-Flux and m5resolver

**Audience:** Software developers  
**Prerequisites:** Python 3.10+, optional PlatformIO for firmware

## 1. Install and launch

```bash
cd host
pip install -e .
```

Users launch the GUI via `Start Utah Flux Studio.bat`. Developers can also run:

```bash
utah-flux-studio
```

## 2. Understand the compile pipeline

1. User builds a project in the GUI (bricks + links).
2. `POST /api/compile` calls `utah_flux.compiler.compile_project`.
3. Compiler output:
   - `intent` — JSON sent to firmware
   - `wires` — reactive mappings for live telemetry (browser applies on tilt)
4. `m5resolver.validation` + `safety` + `simulation` must pass.

Example programmatic compile:

```python
from utah_flux.compiler import compile_project
from utah_flux.templates import get_template

result = compile_project(get_template("tilt_alarm"))
assert result["ok"]
print(result["intent"])
```

## 3. Project file format (`.flux.json`)

```json
{
  "version": 1,
  "name": "My Project",
  "bricks": [
    {"id": "t1", "type": "when_tilt", "x": 60, "y": 60, "params": {}},
    {"id": "a1", "type": "show_message", "x": 60, "y": 200, "params": {"text": "Hi", "color": "green"}}
  ],
  "links": [{"from": "t1", "to": "a1"}]
}
```

## 4. Intent protocol (firmware contract)

See `schemas/intent.schema.json`. Top-level keys:

- `display`, `speaker`, `power`
- `registry` — hot-reload runtime units
- `capability_query` — device capability discovery

Send over serial (115200), one JSON object per line.

## 5. Optional: pyserial controller + agent

For headless or CI bridges:

```python
from m5resolver import IntentController

ctl = IntentController(
    port="COM3",
    registry_path="registry/units.json",
    telemetry_schema_path="schemas/telemetry.schema.json",
    enable_agent=True,
)
ctl.open()
ctl.send_intent({"capability_query": True})
frame = ctl.read_frame()
ctl.close()
```

## 6. Add a custom brick

1. Add spec in `host/utah_flux/bricks.py` (`BRICK_CATALOG`).
2. Implement compile logic in `host/utah_flux/compiler.py`.
3. Restart studio — palette refreshes from `/api/bricks`.

## 7. Run tests

```bash
make quality
# or
pytest
```

## 8. Architecture references

- ADR 0001 — Intent-first
- ADR 0003 — Registry-driven units
- ADR 0004 — Hardware Context Protocol
