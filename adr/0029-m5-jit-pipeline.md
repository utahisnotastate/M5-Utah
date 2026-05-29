# ADR 0029: m5-jit Pipeline Completion

## Status

Accepted — 2026-05-29

## Context

Advanced vibe requirements (custom filters, bit-packing loops) cannot always be expressed
as GPIO/binwire toggles. ADR 0011 introduced RuntimeLinker and HostJitCompiler; this ADR
formalizes the unified **m5-jit** pipeline with differential registry patching (ADR 0014).

## Decision

### Host

- `HostJitCompiler.compile_intent_to_assembly()` — `-fPIC -O3 -nostdlib` Xtensa `.text` extract
- `verify_iram_payload_safe()` — 4096-byte IRAM gate matching firmware
- `M5JitPipeline` — compile → validate → optional `DeltaEncoder` registry patch
- `IntentController.compile_and_send_jit_with_delta()` — JIT intent + 0xDE delta on wire

### Firmware

- `RuntimeLinker` — `MALLOC_CAP_EXEC` IRAM, `resolveNativeJitIntent()`
- `M5Jit.h` — single include documenting JIT + delta paths
- `native_jit` JSON handled on Core 1 via existing M5Kernel JSON dispatch (no main.cpp duplication)

## Consequences

- Capability: `runtime_jit_linker` (existing)
- Tests: `test_instruction_ram_allocation_constraints`, `test_jit_pipeline_with_registry_delta`
- Full flash recompile not required for validated native_jit patches
