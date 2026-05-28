# Architecture

## Runtime split

- **Firmware plane**: deterministic IO execution and telemetry framing
- **Host plane**: intent composition, policy logic, and reactive orchestration
- **Registry plane**: capability and protocol metadata for units

## Protocol

- Transport: serial, 115200 baud
- Message format: newline-delimited JSON
- Frames:
  - telemetry (`type=telemetry`)
  - command acknowledgements (`type=ack`)

## Design constraints

- Keep firmware minimal and stable
- Push fast-changing behavior to host runtime
- Encode hardware variance in registry, not one-off forks
