#pragma once

#include <Arduino.h>
#include <stdint.h>

/** Heap headroom gate for host 2PC transaction prepare/commit. */
class TransactionalCoreManager {
 public:
  static bool evaluateTransactionFeasibility(uint16_t requestedBufferSize);
  static uint16_t estimateRegistryBufferDemand(size_t payloadLen);
};
