# ADR 0004: Hardware Context Protocol (HCP)

- Status: accepted
- Date: 2026-05-28

## Context

The ecosystem needs a vendor-neutral intent language for hardware orchestration.

## Decision

Adopt `registry/units.json` + `schemas/*.schema.json` as the Hardware Context Protocol (HCP) contract surface.

## Consequences

- Third-party units can be integrated via registry metadata and bounty IDs.
- Host runtime validates and simulates updates before silicon execution.
- Firmware remains static while behavior evolves through registry hot reload.
