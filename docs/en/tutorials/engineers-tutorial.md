# Electronics Engineers Tutorial — Hardware Context Protocol

**Audience:** Hardware and systems engineers  
**Goal:** Map physical units into the registry and validate timing/power

## 1. System boundaries

| Layer | Responsibility |
|-------|----------------|
| Firmware | Deterministic IO, telemetry, ACK, registry task supervisor |
| m5resolver | Validation, simulation, agentic remediation |
| Utah-Flux | Human-facing composition → intents |
| Registry | Unit capabilities, addresses, semantic actions |

## 2. Register a new unit

Edit `registry/units.json`:

```json
{
  "unit_id": "my_sensor",
  "bus": "i2c",
  "address": 72,
  "capabilities": ["temperature"],
  "register_map": { "temp_c": "computed" },
  "max_power_ma": 30,
  "priority": 1,
  "bounty_id": "community-my-sensor-v1"
}
```

Validate:

- Schema: `schemas/registry.schema.json`
- CI: `schema-check` workflow

## 3. Semantic actions (firmware)

Firmware maps registry entries to behaviors in `firmware/src/registry_runtime.cpp`:

- `ACTION_INDICATE_STATUS_SUCCESS`
- `ACTION_INDICATE_ALERT`
- `ACTION_REACT_TO_MOTION`

Add new semantics in firmware only when a physical primitive is shared across many units.

## 4. Power and timing gates

Host rejects unsafe configs via `host/m5resolver/safety.py`:

- Max unit frequency (Hz)
- Max estimated power (mA)
- Speaker frequency/duration limits

Simulation estimates draw in `simulation.py` before push.

Telemetry schema includes `metrics.i2c_bandwidth_pct` and `metrics.latency_budget_ms` for future bus saturation checks.

## 5. Bring-up checklist

1. Flash firmware, confirm telemetry at 20 Hz.
2. Send `{"capability_query": true}`, verify ACK capabilities list.
3. Push registry slice: `{"registry": {"units": {...}}}`.
4. Confirm ACK `ok: true` and expected physical behavior.
5. Run agent stress test with `examples/agent_loop.py` (developer tool).

## 6. Compatibility

Track board support in [compatibility-matrix.md](../compatibility-matrix.md).

CoreS3 is the primary target; other boards need profile entries in `firmware/platformio.ini`.
