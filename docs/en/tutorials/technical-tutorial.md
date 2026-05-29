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

## 8. Dynamic bus multiplexing (v0.3.2)

Registry units can declare protocol types without reflashing:

```json
{
  "registry": {
    "units": {
      "port_a_i2c": {
        "type": "I2C",
        "pins": [21, 22],
        "frequency_hz": 100000
      }
    }
  }
}
```

Firmware `DynamicMultiplexer` hot-swaps I2C/SPI/PWM/GPIO. Host `bus_validation` rejects pin conflicts.

## 9. Gossip mesh

```python
from m5resolver import FluxwireGossipMesh

mesh = FluxwireGossipMesh(node_id="lab_node_1")
mesh.start_background()
mesh.update_local_registry({"units": []})
```

Peers discover each other via UDP broadcast and share registry fingerprints.

## 11. Time-travel debugging (v0.3.3)

Firmware journals intent fingerprints + heap on every registry/intent change.  
On low heap, it emits:

```text
[FLUXWIRE_TIME_TRAVEL_STREAM]:{"type":"time_travel_journal_dump",...}
```

Host replay:

```python
from m5resolver import HostReplayEngine

engine = HostReplayEngine()
result = engine.reconstruct_hardware_crash_timeline(journal_json)
if not result.ok:
    print("Fault at", result.fault_fingerprint)
```

`IntentController` intercepts journal lines automatically when `enable_time_travel=True`.

## 12. Architecture references

- ADR 0001 — Intent-first
- ADR 0003 — Registry-driven units
- ADR 0004 — Hardware Context Protocol
