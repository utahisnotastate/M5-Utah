#pragma once

#include <Arduino.h>
#include <stdint.h>

struct __attribute__((packed)) CompactingDeltaHeader {
  uint8_t transactionSequenceId;
  uint16_t dynamicUnitBitmask;
};

constexpr uint8_t kDeltaMagic0 = 0xDE;
constexpr uint8_t kDeltaMagic1 = 0xDA;
constexpr uint8_t kBitmapDeltaMagic0 = 0x23;
constexpr uint8_t kBitmapDeltaMagic1 = 0x44;
constexpr int kMaxDeltaSlots = 16;
constexpr size_t kBitmapDeltaFrameLen = 10;

struct __attribute__((packed)) CompactingBitmapDeltaPacket {
  uint16_t dynamicUnitBitmask;
  uint16_t frequencyHz;
  uint32_t transactionSequenceId;
};

class DeltaEngine {
 public:
  static bool tryProcess(Stream &stream);
  static bool processBitmapDeltaPayload(Stream &stream);
  static void executeCompactedByteMutation(uint16_t bitmask, Stream &dataStream, uint8_t sequenceId);
  static void applyBitmapDeltaMask(uint16_t bitmask, uint16_t frequencyHz, uint32_t sequenceId);
};

void registryApplyDeltaSlot(int slotId, uint16_t frequencyHz, uint8_t sequenceId);

uint16_t registryGetSlotFrequency(int slotId);
