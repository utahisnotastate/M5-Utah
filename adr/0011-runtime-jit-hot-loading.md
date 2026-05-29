# ADR 0011: Dynamic JIT Hot-Loading and Runtime Linker

## Status

Accepted — 2026-05-29

## Context

Some vibe-coded features cannot be expressed via registry GPIO orchestration alone. Requiring
full firmware reflash for custom native routines blocks the intent-first workflow. The platform
needs signed, size-bounded machine code injection into ESP32 executable IRAM.

## Decision

### Feature 21 — RuntimeLinker (firmware)

- Allocate `MALLOC_CAP_EXEC | MALLOC_CAP_32BIT` buffers via `heap_caps_malloc`.
- Decode `payload_hex` intents and bind function pointers for clock-edge execution.
- Hard cap `kMaxCodeBytes = 4096` aligned with host validation.

### Feature 22 — HostJitCompiler (host)

- Cross-compile C snippets with `xtensa-esp32-elf-gcc` (`-fPIC`, `-nostdlib`).
- Extract `.text` via `objcopy`; package as `native_jit` intents.
- `IntentController.compile_and_send_jit()` orchestrates compile → sign → send.

### Feature 23 — JIT validation matrix

- `validate_native_jit_block()` enforces hex integrity, size caps, and alignment.
- Tests reject 8192-byte oversized payloads per safe IRAM profile.

## Consequences

- Executing arbitrary machine code is inherently high risk; sandbox + crypto layers still apply.
- Toolchain must be installed on host for live compilation; hex-only intents work without gcc.
- Injected code must follow Xtensa calling conventions (`void vDynamicTask(void)`).

## References

- ADR 0010 Crypto Enclave
- `firmware/src/RuntimeLinker.h`
- `host/m5resolver/jit_compiler.py`
