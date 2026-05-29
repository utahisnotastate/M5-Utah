# Architecture

## Layers

```
┌─────────────────────────────────────┐
│   Utah Flux Studio (browser GUI)    │  Drag bricks, connect wires, Play
└─────────────────┬───────────────────┘
                  │ compile .flux.json
┌─────────────────▼───────────────────┐
│   Utah-Flux (host/utah_flux)        │  Bricks, templates, compiler
└─────────────────┬───────────────────┘
                  │ validated intents
┌─────────────────▼───────────────────┐
│   m5resolver (host/m5resolver)      │  Safety, simulation, agent, registry
└─────────────────┬───────────────────┘
                  │ JSON over serial (WebSerial or USB)
┌─────────────────▼───────────────────┐
│   Firmware (firmware/)              │  Intent execution, registry hot-reload
└─────────────────────────────────────┘
```

## Design principles

- **Intent-first** — describe desired device state, not register polling loops.
- **Registry-first** — hardware differences live in `registry/units.json`.
- **Compiled configuration** — AI/rules produce registry/intent JSON, not one-off C++ per project.
- **Safety gate** — validation + simulation before hardware receives updates.

## Protocol

- Transport: USB serial @ 115200 (WebSerial in browser)
- Framing: newline-delimited JSON
- Types: `telemetry`, `ack`, intents (`display`, `speaker`, `power`, `registry`)
