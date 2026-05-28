# ADR 0001: Intent-First Architecture

- Status: accepted
- Date: 2026-05-28

## Context

Module-specific imperative APIs created duplicated logic and fragmented developer workflows.

## Decision

Adopt an intent-first architecture where host-side logic sends declarative JSON intents and firmware executes deterministic hardware actions.

## Consequences

- Faster iteration by reducing firmware reflashing frequency
- Cleaner separation between policy logic and hardware execution
- Requires stable contracts and schema governance
