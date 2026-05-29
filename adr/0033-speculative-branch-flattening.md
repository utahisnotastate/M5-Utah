# ADR 0033: Speculative Branch-Flattening Jump Matrix (m5-flatten)

## Status

Accepted — 2026-05-29

## Context

Dynamic vibe-driven conditionals stall embedded pipelines via branch misprediction and
deep nesting. ADR 0002 (Thin Firmware Boundary) requires host-side compilation of logic
into fixed binary frames consumed without JSON heap allocation on device.

## Decision

### Host — `BranchFlattenCompiler`

- Wire magic: `#F` (`0x23 0x46`), 6-byte fixed frame
- Payload: `!BBH` — condition index, function slot, priority mask
- `IntentController.send_branch_flatten()` and `UnifiedOrchestrationController.synchronize_branch_flatten()`

### Firmware — `MicroJumpKernel`

- Lockless `BranchStateMirrorEntry` array indexed by condition id
- Pre-allocated `g_jumpTableMatrix[16]` function-pointer table
- Core 0 CrossCorePipe demux → ring → Core 1 `processPayload()` dispatch
- Priority gatekeeper wraps indirect jumps when bus contention requires inheritance

## Consequences

- Capability: `speculative_branch_flattening`
- Test: `test_branch_flatten_packing_contracts` in `tests/test_validation.py`
- Does not replace JSON intent path or RPP micro-execution kernel
