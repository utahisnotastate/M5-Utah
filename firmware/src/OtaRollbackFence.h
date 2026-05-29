#pragma once

#include <stdint.h>

/** Double-buffered OTA rollback fence (m5-rollback). */
class OtaRollbackFence {
 public:
  void initializePassiveStoragePartition();
  bool verifyAndCommitOtaState();
  bool hasPassivePartition() const;
  uint32_t passivePartitionAddress() const;

 private:
  void *updatePartition_ = nullptr;
  void *otaHandle_ = nullptr;
  bool initialized_ = false;
};

void otaRollbackFenceInit();
OtaRollbackFence &globalOtaRollbackFence();
