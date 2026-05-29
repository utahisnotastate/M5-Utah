#pragma once

#include <stddef.h>
#include <stdint.h>

typedef void (*VibeCompiledFunction)(void);

class RuntimeLinker {
 public:
  static RuntimeLinker &instance();

  static constexpr size_t kMaxCodeBytes = 4096;

  bool injectNativeMachineBytes(const uint8_t *machineCode, size_t codeSize);
  bool injectFromHexPayload(const char *payloadHex, size_t declaredSize);
  void executeActiveFunctionHook();
  bool hasActiveHook() const;
  size_t activeCodeSize() const;
  void *activeCodePointer() const;

 private:
  RuntimeLinker() = default;

  VibeCompiledFunction activeHotFunction_ = nullptr;
  uint8_t *executableMemoryBuffer_ = nullptr;
  size_t allocatedSize_ = 0;
};

RuntimeLinker &nativeLinker();

bool resolveNativeJitIntent(const char *payloadHex, size_t declaredSize, bool execute);
