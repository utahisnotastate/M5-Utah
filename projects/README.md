# Utah Flux Projects

Save and open `.flux.json` project files from **Utah Flux Studio** using the Save/Open buttons.

## Example projects

| File | Format | Description |
|------|--------|-------------|
| `hello.flux.json` | `bricks` + `links` | Simple welcome screen (Lego Studio) |
| `sanctum.flux.json` | `nodes` + `bindings` | Field-graph Sanctum UI with IMU-driven colors |

## Lego format (`bricks` / `links`)

Open in Utah Flux Studio → drag, wire, Play. Compiled by `host/utah_flux/compiler.py`.

## Field graph format (`nodes` / `bindings`)

Used for advanced layouts (e.g. `Sanctum_Voxel_Alpha`). Compiled by `host/utah_flux/field_compiler.py`:

- Display elements ship to firmware as `display.elements[]`
- Wire bindings (e.g. IMU → label color) stay **host-side** — not emitted as `registry` units

See [docs/en/field-graph-compiler.md](../docs/en/field-graph-compiler.md).

## Tests

```text
py -m pytest tests/test_field_compiler.py -q
```
