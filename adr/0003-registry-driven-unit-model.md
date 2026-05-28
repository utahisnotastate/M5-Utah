# ADR 0003: Registry-Driven Unit Model

- Status: accepted
- Date: 2026-05-28

## Context

Per-unit repository patterns cause duplication and increase lifecycle overhead.

## Decision

Represent unit capabilities and protocol metadata in a shared JSON registry (`registry/units.json`) with runtime loading.

## Consequences

- Unit support scales through metadata and shared runtime patterns
- Easier inventory, compatibility tracking, and migration planning
- Requires careful schema discipline and release governance
