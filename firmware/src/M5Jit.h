#pragma once

/**
 * m5-jit — Position-Independent Machine-Byte Hot-Loading
 *
 * RuntimeLinker allocates MALLOC_CAP_EXEC IRAM, binds VibeCompiledFunction hooks,
 * and executes on clock edge without reboot. Wired from native_jit JSON intents
 * on Core 1 (M5Kernel) — do not duplicate linker logic in main.cpp loops.
 *
 * Differential registry patching uses DeltaEngine (0xDE 0xDA) on Core 0 ingest.
 *
 * See adr/0011-runtime-jit-hot-loading.md and adr/0014-dag-state-graph-and-delta-compression.md
 */

#include "RuntimeLinker.h"
#include "DeltaEngine.h"

inline RuntimeLinker &m5JitLinker() { return nativeLinker(); }

inline bool m5JitLoadFromHex(const char *payloadHex, size_t declaredSize, bool execute) {
  return resolveNativeJitIntent(payloadHex, declaredSize, execute);
}

inline void m5JitExecuteHook() { nativeLinker().executeActiveFunctionHook(); }
