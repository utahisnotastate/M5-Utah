#include "VectorFence.h"

#include "TimeTravelJournal.h"

#include <cstring>
#include <esp_heap_caps.h>
#include <freertos/FreeRTOS.h>

namespace {

UnwrappedInterruptRoutine g_dynamicIsrVectorTable[kMaxVectorChannels] = {};
uint8_t *g_executionAllocationsPool[kMaxVectorChannels] = {nullptr, nullptr, nullptr, nullptr};

bool readExact(Stream &stream, uint8_t *buffer, size_t len) {
  size_t offset = 0;
  const uint32_t start = millis();
  while (offset < len) {
    if (stream.available() > 0) {
      const int ch = stream.read();
      if (ch < 0) {
        return false;
      }
      buffer[offset++] = static_cast<uint8_t>(ch);
      continue;
    }
    if (millis() - start > 100) {
      return false;
    }
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

void vectorFenceInit() { VectorFenceEngine::initDefaults(); }

void VectorFenceEngine::initDefaults() {
  for (int i = 0; i < kMaxVectorChannels; ++i) {
    g_dynamicIsrVectorTable[i] = nullptr;
    if (g_executionAllocationsPool[i] != nullptr) {
      heap_caps_free(g_executionAllocationsPool[i]);
      g_executionAllocationsPool[i] = nullptr;
    }
  }
}

UnwrappedInterruptRoutine VectorFenceEngine::getRoutine(uint8_t channel) {
  if (channel >= kMaxVectorChannels) {
    return nullptr;
  }
  return g_dynamicIsrVectorTable[channel];
}

bool VectorFenceEngine::applyVectorPatch(uint8_t channel, const uint8_t *code, size_t length,
                                         uint32_t transactionId) {
  if (channel >= kMaxVectorChannels || code == nullptr || length == 0 ||
      length > kMaxVectorPatchPayload) {
    return false;
  }

  Serial.printf("[VECTOR FENCE] Relocating interrupt channel %u. Length: %u bytes\n", channel,
                static_cast<unsigned>(length));
  (void)transactionId;

  if (g_executionAllocationsPool[channel] != nullptr) {
    heap_caps_free(g_executionAllocationsPool[channel]);
    g_executionAllocationsPool[channel] = nullptr;
  }

  g_executionAllocationsPool[channel] =
      static_cast<uint8_t *>(heap_caps_malloc(length, MALLOC_CAP_32BIT | MALLOC_CAP_EXEC));
  if (g_executionAllocationsPool[channel] == nullptr) {
    Serial.println("[CRITICAL ERROR] Executable IRAM limits exhausted!");
    return false;
  }

  memcpy(g_executionAllocationsPool[channel], code, length);

  portDISABLE_INTERRUPTS();
  g_dynamicIsrVectorTable[channel] =
      reinterpret_cast<UnwrappedInterruptRoutine>(g_executionAllocationsPool[channel]);
  portENABLE_INTERRUPTS();

  timeTravelRecord("vector:isr_patch");
  Serial.println("[SUCCESS] Dynamic hardware interrupt vector committed to active silicon.");
  return true;
}

bool VectorFenceEngine::processPayload(Stream &stream) {
  VectorPatchHeader header{};
  if (!readExact(stream, reinterpret_cast<uint8_t *>(&header), sizeof(header))) {
    return false;
  }

  const uint8_t channel = header.interruptSourceId;
  const uint16_t length = ntohs16(header.codeByteLength);
  const uint32_t transactionId = ntohl32(header.transactionId);

  if (channel >= kMaxVectorChannels || length == 0 || length > kMaxVectorPatchPayload) {
    Serial.println("[VECTOR FENCE] Rejected patch: channel or length out of bounds.");
    for (uint16_t i = 0; i < length && stream.available() > 0; ++i) {
      stream.read();
    }
    return false;
  }

  uint8_t buffer[kMaxVectorPatchPayload];
  if (!readExact(stream, buffer, length)) {
    return false;
  }

  return applyVectorPatch(channel, buffer, length, transactionId);
}
