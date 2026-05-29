# ADR 0005: Dynamic Bus Multiplexing and Gossip Mesh

- Status: accepted
- Date: 2026-05-28

## Context

Developers must reflash when changing pin protocols (GPIO vs I2C vs PWM). Central MQTT brokers add latency and single points of failure.

## Decision

1. **Firmware DynamicMultiplexer** — hot-swap I2C, SPI, PWM, GPIO from registry units at runtime via ESP32 GPIO matrix routing.
2. **Host bus_validation** — reject pin conflicts and invalid protocol maps before deployment.
3. **FluxwireGossipMesh** — UDP peer gossip for registry fingerprints and degraded-state relay.

## Consequences

- Protocol changes become registry updates, not C++ recompiles.
- Multi-device rooms can share state without a cloud broker.
- Validation must stay strict to prevent unsafe pin maps.
