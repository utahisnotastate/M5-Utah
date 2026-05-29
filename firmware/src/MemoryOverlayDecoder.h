#pragma once

#include <Arduino.h>
#include <stdint.h>

enum class OverlayProcessResult { NotOverlay = 0, Applied = 1, Rejected = 2 };

constexpr uint8_t kOverlayMagic0 = 0x23;
constexpr uint8_t kOverlayMagic1 = 0x4D;
constexpr uint32_t kIramExecStart = 0x40080000UL;
constexpr uint32_t kIramExecEnd = 0x400A0000UL;
constexpr size_t kMaxOverlayPayload = 4096;

class MemoryOverlayDecoder {
 public:
  static OverlayProcessResult tryProcess(Stream &stream);
  static OverlayProcessResult processPayload(Stream &stream);
  static bool isAddressExecutable(uint32_t address);
};

bool applyMemoryOverlay(uint32_t targetAddress, const uint8_t *instructions, size_t length,
                        bool installHook);
