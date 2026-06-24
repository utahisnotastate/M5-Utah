# Field Graph Compiler (Sanctum / Nodes + Bindings)

Some projects use a **field graph** layout (`nodes`, `bindings`, `layout`) instead of the classic Lego `bricks` + `links` format. The host compiler in `host/utah_flux/field_compiler.py` converts these graphs into device-safe display intents.

## When to use

| Format | Keys | Studio | Compiler |
|--------|------|--------|----------|
| Lego bricks | `bricks`, `links` | Utah Flux Studio GUI | `utah_flux/compiler.py` |
| Field graph | `nodes`, `bindings` | External injector or API | `utah_flux/field_compiler.py` |

Example: `projects/sanctum.flux.json` — multi-element UI with IMU-driven label colors.

## Compile pipeline

1. **Detect** — `is_field_graph_flux()` returns true when `nodes` or `bindings` are present (and no `bricks`).
2. **Layout** — `layout.type` (e.g. `Sanctum_Voxel_Alpha`) selects element placement.
3. **Display intent** — nodes become `display.elements[]` (labels, rects, status chips).
4. **Bindings** — wire expressions stay **host-side**; they are not emitted as firmware `registry` units.
5. **Validate** — `validate_intent_payload`, `validate_intent_safety`, `HardwareSimulator.simulate_intent`.

## Color handling

Hex colors like `#FF0000` are converted to RGB565 (`0xF800`) via `rgb888_to_rgb565()` — required for M5 display hardware.

## Host-only bindings

Bindings such as `imu_coherence → status_label.color` are evaluated on the host against live telemetry. They are **not** compiled into `registry` blocks on the device (avoids unnecessary sandbox units and CoreS3 crashes).

## Testing

```text
py -m pytest tests/test_field_compiler.py -q
```

## Related

- `projects/sanctum.flux.json`
- [Technical users](technical-users.md)
- [Omega defense stack](omega-defense-stack.md) — optional `ephemeral_store` for sensitive params
