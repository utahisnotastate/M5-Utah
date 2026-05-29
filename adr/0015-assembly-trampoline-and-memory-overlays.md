# ADR 0015: Assembly Trampolines and Differential Memory Overlays

## Status

Accepted — 2026-05-29

## Context

Runtime JIT injection loads new machine code into IRAM but does not redirect execution from
existing compiled C++ functions without a full re-flash. Host orchestration also needs a compact
binary path for localized instruction patches rather than full registry JSON reloads.

## Decision

### Feature 33 — AssemblyHook (firmware)

- `AssemblyHook` stores the first four bytes of a target function, writes a position-independent
  jump stub under interrupt disable, and restores on unhook.
- `MemoryOverlayDecoder` validates IRAM address fences (`0x40080000`–`0x400A0000`), injects payload
  via `RuntimeLinker`, then applies trampoline to the hook target (or `nativeHookProbe` fallback).
- Wire magic `#M` (`0x23 0x4D`) with big-endian address + length header.

### Feature 34 — HardwareMemoryCompiler (host)

- `compile_memory_overlay()` packs magic + metadata + raw instruction bytes.
- `DriverRegistry.compile_overlay_for_unit()` builds frames from registry unit records.
- `IntentController.send_memory_overlay()` transmits validated overlays on the serial link.

### Feature 35 — Address fence validation (tests)

- `verify_address_safety()` enforced on compile and in `tests/test_validation.py`.
- Dedicated `tests/test_memory_compiler.py` for frame layout and round-trip unpack.

### Binary demux order (firmware)

Serial transport demuxes by leading bytes: delta (`0xDE`), then shared `0x23` prefix disambiguated
by second byte (`0x4D` overlay vs `0x23` binwire).

## Consequences

- Capabilities: `assembly_trampoline_hook`, `memory_overlay_compiler`.
- Overlay and binwire share first magic byte; firmware must consume both header bytes before routing.
- Trampoline patching is architecture-specific (Xtensa stub simulation); production hooks require
  validated instruction encodings for the target SoC.
