# ADR 0031: Bitmapped Graph-Relational Delta Overlays

## Status

Accepted — 2026-05-29

## Context

ADR 0014 introduced multi-slot `0xDE 0xDA` delta frames with per-slot frequency payloads.
Mesh operators also need ultra-lean single-frequency overlays when a vibe mutation touches
one registry slot — without JSON traversal or variable-length slot lists.

## Decision

### Host — `BitmappedDeltaCompiler`

- Wire magic: `#D` (`0x23 0x44`), 10-byte fixed frame
- Payload: `!HHI` — 16-bit bitmask, 16-bit frequency Hz, 32-bit sequence id
- `IntentController.send_bitmap_delta()` streams compact overlays on Fluxwire

### Firmware — `DeltaEngine::processBitmapDeltaPayload`

- Core 0 `CrossCorePipe` demuxes `#D` before `#M` / `#P` / `##`
- Core 1 applies all set bits with shared frequency via `registryApplyDeltaSlot()`
- Existing `0xDE 0xDA` multi-slot path unchanged

## Consequences

- Capability: `bitmapped_graph_relational_delta`
- Test: `test_bitmapped_delta_packing_contracts` in `tests/test_registry.py`
- Complements (does not replace) graph cascade encoding in `DeltaEncoder`
