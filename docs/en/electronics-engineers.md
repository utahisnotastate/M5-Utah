# Electronics Engineer Guide

## Engineering boundary

- Firmware plane: deterministic IO, telemetry framing, ACK responses
- Host plane: intent policy, transformations, orchestration
- Registry plane: unit capabilities and protocol metadata

## Protocol

- serial transport: 115200
- newline-delimited JSON frames
- telemetry: `type=telemetry`
- acknowledgements: `type=ack`

## Migration checklist

1. Inventory legacy module repos
2. Map active units into registry
3. Port golden-path examples to intent flows
4. Keep legacy repos in bridge/reference mode only
