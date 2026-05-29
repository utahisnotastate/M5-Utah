#include "TransactionalCoreManager.h"

#include <Arduino.h>

bool TransactionalCoreManager::evaluateTransactionFeasibility(uint16_t requestedBufferSize) {
  const uint32_t availableHeap = ESP.getFreeHeap();
  const uint32_t headroomLimit = static_cast<uint32_t>(availableHeap * 0.3f);

  if (requestedBufferSize > headroomLimit) {
    Serial.println("[TRANSACTION REJECTED] Requested allocation threatens heap boundaries!");
    return false;
  }

  Serial.println("[TRANSACTION APPROVED] Node resource footprint verified stable.");
  return true;
}

uint16_t TransactionalCoreManager::estimateRegistryBufferDemand(size_t payloadLen) {
  if (payloadLen == 0) {
    return 512;
  }
  if (payloadLen > 65535) {
    return 65535;
  }
  return static_cast<uint16_t>(payloadLen);
}
