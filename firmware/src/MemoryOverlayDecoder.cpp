#include "MemoryOverlayDecoder.h"

#include "AssemblyHook.h"
#include "RuntimeLinker.h"
#include "TimeTravelJournal.h"

#include <esp_heap_caps.h>

namespace {

bool readExact(Stream &stream, uint8_t *buffer, size_t len) {
  size_t offset = 0;
  uint32_t start = millis();
  while (offset < len) {
    if (stream.available() > 0) {
      int ch = stream.read();
      if (ch < 0) return false;
      buffer[offset++] = static_cast<uint8_t>(ch);
      continue;
    }
    if (millis() - start > 100) return false;
    delay(1);
  }
  return true;
}

uint32_t readU32Be(Stream &stream) {
  uint8_t buf[4];
  if (!readExact(stream, buf, 4)) return 0;
  return (static_cast<uint32_t>(buf[0]) << 24) | (static_cast<uint32_t>(buf[1]) << 16) |
         (static_cast<uint32_t>(buf[2]) << 8) | static_cast<uint32_t>(buf[3]);
}

}  // namespace

bool MemoryOverlayDecoder::isAddressExecutable(uint32_t address) {
  return address >= kIramExecStart && address <= kIramExecEnd;
}

bool applyMemoryOverlay(uint32_t targetAddress, const uint8_t *instructions, size_t length,
                        bool installHook) {
  if (instructions == nullptr || length == 0 || length > kMaxOverlayPayload) {
    return false;
  }

  if (!nativeLinker().injectNativeMachineBytes(instructions, length)) {
    return false;
  }

  void *newFunc = nativeLinker().activeCodePointer();
  if (newFunc == nullptr) {
    return false;
  }

  Serial.printf("[OVERLAY] Mapped %u bytes (hook target 0x%08X)\n", length, targetAddress);

  if (installHook) {
    void *hookTarget = MemoryOverlayDecoder::isAddressExecutable(targetAddress)
                           ? reinterpret_cast<void *>(targetAddress)
                           : reinterpret_cast<void *>(nativeHookProbe);
    return loopDetour().applyTrampolineHook(hookTarget, newFunc);
  }

  nativeLinker().executeActiveFunctionHook();
  return true;
}

OverlayProcessResult MemoryOverlayDecoder::processPayload(Stream &stream) {
  const uint32_t targetAddress = readU32Be(stream);
  const uint32_t payloadLength = readU32Be(stream);
  if (payloadLength == 0 || payloadLength > kMaxOverlayPayload) {
    Serial.println("[OVERLAY] Invalid payload length.");
    return OverlayProcessResult::Rejected;
  }

  if (!isAddressExecutable(targetAddress)) {
    Serial.printf("[OVERLAY REJECTED] Address 0x%08X outside IRAM execution fence.\n",
                  targetAddress);
    timeTravelRecord("overlay:reject");
    for (uint32_t i = 0; i < payloadLength && stream.available() > 0; i++) {
      stream.read();
    }
    return OverlayProcessResult::Rejected;
  }

  uint8_t buffer[kMaxOverlayPayload];
  if (!readExact(stream, buffer, payloadLength)) {
    return OverlayProcessResult::Rejected;
  }

  timeTravelRecord("overlay:apply");
  if (applyMemoryOverlay(targetAddress, buffer, payloadLength, true)) {
    return OverlayProcessResult::Applied;
  }
  return OverlayProcessResult::Rejected;
}

OverlayProcessResult MemoryOverlayDecoder::tryProcess(Stream &stream) {
  if (stream.available() < 10) return OverlayProcessResult::NotOverlay;
  if (stream.peek() != kOverlayMagic0) return OverlayProcessResult::NotOverlay;

  uint8_t magic[2];
  if (!readExact(stream, magic, 2)) return OverlayProcessResult::NotOverlay;
  if (magic[0] != kOverlayMagic0 || magic[1] != kOverlayMagic1) {
    return OverlayProcessResult::NotOverlay;
  }

  return processPayload(stream);
}
