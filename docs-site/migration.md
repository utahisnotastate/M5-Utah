# Migration

## From many M5Stack libraries → Utah Flux

| Old way | Utah Flux way |
|---------|----------------|
| Clone per-unit repo | Drag bricks in Studio |
| Edit C++ and reflash | Press Play (intent update) |
| Remember driver APIs | Read `registry/units.json` |
| Debug compile errors | Visual wires + live log |

## For organizations

1. Flash unified firmware once per device line.
2. Standardize on `.flux.json` project files for curriculum and support.
3. Classify legacy repos as reference/bridge/retired (see employee playbook).
