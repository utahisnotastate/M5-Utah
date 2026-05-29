#pragma once

#include <Arduino.h>
#include <stdint.h>

struct __attribute__((packed)) VectorPatchHeader {
  uint8_t interruptSourceId;
  uint16_t codeByteLength;
  uint32_t transactionId;
};

using UnwrappedInterruptRoutine = void (*)();

static constexpr uint8_t kVectorFenceMagic0 = 0x23;
static constexpr uint8_t kVectorFenceMagic1 = 0x49;
static constexpr int kMaxVectorChannels = 4;
static constexpr size_t kMaxVectorPatchPayload = 512;
static constexpr size_t kVectorPatchHeaderLen = sizeof(VectorPatchHeader);

/** Hot-swappable IRAM interrupt vector fence (m5-vectorfence). */
class VectorFenceEngine {
 public:
  static bool processPayload(Stream &stream);
  static bool applyVectorPatch(uint8_t channel, const uint8_t *code, size_t length,
                               uint32_t transactionId);
  static UnwrappedInterruptRoutine getRoutine(uint8_t channel);
  static void initDefaults();
};

void vectorFenceInit();
