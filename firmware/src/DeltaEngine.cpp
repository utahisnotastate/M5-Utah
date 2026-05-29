#include "DeltaEngine.h"

#include "TimeTravelJournal.h"
#include "registry_runtime.h"

#include <cstring>

namespace {

uint16_t g_slotFrequencies[kMaxDeltaSlots];
bool g_slotActive[kMaxDeltaSlots];

uint16_t readU16Be(Stream &stream) {
  const int hi = stream.read();
  const int lo = stream.read();
  if (hi < 0 || lo < 0) return 0;
  return static_cast<uint16_t>((hi << 8) | lo);
}

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
    if (millis() - start > 50) return false;
    delay(1);
  }
  return true;
}

uint16_t ntohs16(uint16_t value) {
  return static_cast<uint16_t>(((value & 0xFF00) >> 8) | ((value & 0x00FF) << 8));
}

uint32_t ntohl32(uint32_t value) {
  return ((value & 0xFF000000U) >> 24) | ((value & 0x00FF0000U) >> 8) |
         ((value & 0x0000FF00U) << 8) | ((value & 0x000000FFU) << 24);
}

}  // namespace

void registryApplyDeltaSlot(int slotId, uint16_t frequencyHz, uint8_t sequenceId) {
  if (slotId < 0 || slotId >= kMaxDeltaSlots) return;

  g_slotFrequencies[slotId] = frequencyHz;
  g_slotActive[slotId] = true;

  char unitName[16];
  snprintf(unitName, sizeof(unitName), "slot_%d", slotId);
  registryApplyBinwireUnit(unitName, static_cast<uint8_t>(slotId + 2), frequencyHz, sequenceId);
}

uint16_t registryGetSlotFrequency(int slotId) {
  if (slotId < 0 || slotId >= kMaxDeltaSlots) return 0;
  return g_slotFrequencies[slotId];
}

void DeltaEngine::applyBitmapDeltaMask(uint16_t bitmask, uint16_t frequencyHz,
                                       uint32_t sequenceId) {
  Serial.printf("[DELTA ENGINE FASTPATH] Decoded Mask: 0x%04X -> Target Freq: %u Hz\n", bitmask,
                frequencyHz);
  timeTravelRecord("delta:bitmap");

  const uint8_t seqByte = static_cast<uint8_t>(sequenceId & 0xFF);
  for (int slotId = 0; slotId < kMaxDeltaSlots; slotId++) {
    if ((bitmask >> slotId) & 0x01) {
      Serial.printf(" -> Hot-patching registration parameter on slot index: %d\n", slotId);
      registryApplyDeltaSlot(slotId, frequencyHz, seqByte);
    }
  }
}

bool DeltaEngine::processBitmapDeltaPayload(Stream &stream) {
  CompactingBitmapDeltaPacket packet{};
  if (!readExact(stream, reinterpret_cast<uint8_t *>(&packet), sizeof(packet))) {
    return false;
  }

  const uint16_t mask = ntohs16(packet.dynamicUnitBitmask);
  const uint16_t frequency = ntohs16(packet.frequencyHz);
  const uint32_t sequence = ntohl32(packet.transactionSequenceId);
  applyBitmapDeltaMask(mask, frequency, sequence);
  return true;
}

void DeltaEngine::executeCompactedByteMutation(uint16_t bitmask, Stream &dataStream,
                                                uint8_t sequenceId) {
  Serial.printf("[DELTA ENGINE] Parsing incoming bitmapped mutations. Mask: 0x%04X\n", bitmask);
  timeTravelRecord("delta:mutation");

  for (int slotId = 0; slotId < kMaxDeltaSlots; slotId++) {
    if ((bitmask >> slotId) & 0x01) {
      Serial.printf(" -> Hot-patching slot %d\n", slotId);
      if (dataStream.available() >= 2) {
        const uint16_t frequency = readU16Be(dataStream);
        Serial.printf("    [UPDATED] Slot %d frequency -> %u Hz\n", slotId, frequency);
        registryApplyDeltaSlot(slotId, frequency, sequenceId);
      }
    }
  }
}

bool DeltaEngine::tryProcess(Stream &stream) {
  if (stream.available() < 3) return false;
  if (stream.peek() != kDeltaMagic0) return false;

  uint8_t magic[2];
  if (!readExact(stream, magic, 2)) return false;
  if (magic[0] != kDeltaMagic0 || magic[1] != kDeltaMagic1) return false;

  CompactingDeltaHeader header;
  if (!readExact(stream, reinterpret_cast<uint8_t *>(&header), sizeof(CompactingDeltaHeader))) {
    return false;
  }

  const uint16_t bitmask = ntohs16(header.dynamicUnitBitmask);
  executeCompactedByteMutation(bitmask, stream, header.transactionSequenceId);
  return true;
}
