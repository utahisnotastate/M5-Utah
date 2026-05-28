# ADR 0002: Thin Firmware Boundary

- Status: accepted
- Date: 2026-05-28

## Context

Putting business logic in firmware creates brittle release cycles and difficult cross-board maintenance.

## Decision

Keep firmware as a thin runtime for telemetry, intent execution, and ACK framing. Move policy and transformations to host runtime.

## Consequences

- Better maintainability and portability
- Firmware remains stable and testable
- Host runtime must provide robust validation and error handling
