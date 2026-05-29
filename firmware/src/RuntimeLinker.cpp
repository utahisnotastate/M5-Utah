#include "RuntimeLinker.h"

#include "TimeTravelJournal.h"

#include <Arduino.h>
#include <esp_heap_caps.h>

#include <cstring>

namespace {

size_t decodeHexByte(char c) {
  if (c >= '0' && c <= '9') return c - '0';
  if (c >= 'a' && c <= 'f') return c - 'a' + 10;
  if (c >= 'A' && c <= 'F') return c - 'A' + 10;
  return SIZE_MAX;
}

size_t decodeHexPayload(const char *hex, uint8_t *out, size_t outMax) {
  if (hex == nullptr) return 0;
  size_t hexLen = strlen(hex);
  if (hexLen == 0 || (hexLen % 2) != 0) return 0;

  size_t byteCount = hexLen / 2;
  if (byteCount > outMax) return 0;

  for (size_t i = 0; i < byteCount; ++i) {
    size_t hi = decodeHexByte(hex[i * 2]);
    size_t lo = decodeHexByte(hex[i * 2 + 1]);
    if (hi > 15 || lo > 15) return 0;
    out[i] = static_cast<uint8_t>((hi << 4) | lo);
  }
  return byteCount;
}

void syncExecutableMemory(uint8_t *addr, size_t len) {
#if defined(__XTENSA__)
  __asm__ __volatile__("memw" ::: "memory");
  (void)addr;
  (void)len;
#else
  (void)addr;
  (void)len;
#endif
}

}  // namespace

RuntimeLinker &RuntimeLinker::instance() {
  static RuntimeLinker linker;
  return linker;
}

RuntimeLinker &nativeLinker() { return RuntimeLinker::instance(); }

bool RuntimeLinker::injectNativeMachineBytes(const uint8_t *machineCode, size_t codeSize) {
  Serial.printf("[LINKER] Allocating executable IRAM buffer space: %u bytes\n", codeSize);

  if (machineCode == nullptr || codeSize == 0 || codeSize > kMaxCodeBytes) {
    Serial.println("[CRITICAL ERROR] Invalid machine code size for IRAM injection.");
    return false;
  }

  if (executableMemoryBuffer_ != nullptr) {
    heap_caps_free(executableMemoryBuffer_);
    activeHotFunction_ = nullptr;
    executableMemoryBuffer_ = nullptr;
    allocatedSize_ = 0;
  }

  executableMemoryBuffer_ =
      static_cast<uint8_t *>(heap_caps_malloc(codeSize, MALLOC_CAP_32BIT | MALLOC_CAP_EXEC));
  if (executableMemoryBuffer_ == nullptr) {
    Serial.println("[CRITICAL ERROR] Failed to allocate executable memory caps region!");
    return false;
  }

  memcpy(executableMemoryBuffer_, machineCode, codeSize);
  syncExecutableMemory(executableMemoryBuffer_, codeSize);

  activeHotFunction_ = reinterpret_cast<VibeCompiledFunction>(executableMemoryBuffer_);
  allocatedSize_ = codeSize;
  timeTravelRecord("jit:inject");
  Serial.println("[SUCCESS] Dynamic execution vector bound smoothly. Ready for clock-edge trigger.");
  return true;
}

bool RuntimeLinker::injectFromHexPayload(const char *payloadHex, size_t declaredSize) {
  uint8_t buffer[kMaxCodeBytes];
  size_t decoded = decodeHexPayload(payloadHex, buffer, sizeof(buffer));
  if (decoded == 0) {
    return false;
  }
  if (declaredSize > 0 && declaredSize != decoded) {
    Serial.println("[LINKER] Declared code_size_bytes does not match payload_hex length.");
    return false;
  }
  return injectNativeMachineBytes(buffer, decoded);
}

void RuntimeLinker::executeActiveFunctionHook() {
  if (activeHotFunction_ != nullptr) {
    timeTravelRecord("jit:execute");
    activeHotFunction_();
  }
}

bool RuntimeLinker::hasActiveHook() const { return activeHotFunction_ != nullptr; }

size_t RuntimeLinker::activeCodeSize() const { return allocatedSize_; }

void *RuntimeLinker::activeCodePointer() const {
  return static_cast<void *>(executableMemoryBuffer_);
}

bool resolveNativeJitIntent(const char *payloadHex, size_t declaredSize, bool execute) {
  if (!nativeLinker().injectFromHexPayload(payloadHex, declaredSize)) {
    return false;
  }
  if (execute) {
    nativeLinker().executeActiveFunctionHook();
  }
  return true;
}
