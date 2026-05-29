# Electronics Engineer Guide

## Role in Utah Flux

You own **physical truth** in the registry: bus, address, capabilities, power budgets, and semantic actions.

## Full tutorial

See [Engineers Tutorial](tutorials/engineers-tutorial.md).

## Firmware responsibilities

- Intent execution and ACK framing
- Registry hot-reload with FreeRTOS unit supervisor (`registry_runtime.cpp`)
- Telemetry: `status`, `metrics.free_heap`, IMU, battery

## Host responsibilities (not firmware)

- Policy, composition, safety validation
- Utah Flux visual compiler
- Agentic remediation

## Protocol

- Serial 115200, newline JSON
- Telemetry `type=telemetry`, ACK `type=ack`

## Registry example

See `registry/units.json` and `schemas/registry.schema.json`.

## Migration

Port units to registry entries; stop adding per-SKU imperative drivers for new features.
