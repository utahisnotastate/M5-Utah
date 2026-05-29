#include "OtaRollbackFence.h"

#include <Arduino.h>

#if defined(ESP_PLATFORM)
#include <esp_ota_ops.h>
#include <esp_system.h>
#endif

namespace {

OtaRollbackFence g_otaRollbackFence;

}  // namespace

OtaRollbackFence &globalOtaRollbackFence() { return g_otaRollbackFence; }

void otaRollbackFenceInit() { g_otaRollbackFence.initializePassiveStoragePartition(); }

void OtaRollbackFence::initializePassiveStoragePartition() {
#if defined(ESP_PLATFORM)
  const esp_partition_t *partition = esp_ota_get_next_update_partition(nullptr);
  if (partition == nullptr) {
    Serial.println("[ROLLBACK FENCE] No passive OTA partition configured — fence dormant.");
    initialized_ = false;
    return;
  }

  updatePartition_ = const_cast<esp_partition_t *>(partition);
  esp_ota_handle_t handle = 0;
  const esp_err_t err = esp_ota_begin(partition, OTA_SIZE_UNKNOWN, &handle);
  if (err != ESP_OK) {
    Serial.printf("[ROLLBACK FENCE] Passive partition begin failed: %d\n", static_cast<int>(err));
    initialized_ = false;
    return;
  }

  otaHandle_ = reinterpret_cast<void *>(static_cast<uintptr_t>(handle));
  initialized_ = true;
  Serial.printf("[ROLLBACK FENCE] Safe partition allocated at offset: 0x%08X\n",
                partition->address);
#else
  initialized_ = false;
#endif
}

bool OtaRollbackFence::hasPassivePartition() const { return initialized_; }

uint32_t OtaRollbackFence::passivePartitionAddress() const {
#if defined(ESP_PLATFORM)
  if (updatePartition_ == nullptr) {
    return 0;
  }
  return static_cast<const esp_partition_t *>(updatePartition_)->address;
#else
  return 0;
#endif
}

bool OtaRollbackFence::verifyAndCommitOtaState() {
#if defined(ESP_PLATFORM)
  if (!initialized_ || updatePartition_ == nullptr || otaHandle_ == nullptr) {
    return false;
  }

  const esp_ota_handle_t handle =
      static_cast<esp_ota_handle_t>(reinterpret_cast<uintptr_t>(otaHandle_));
  if (esp_ota_end(handle) != ESP_OK) {
    Serial.println("[ROLLBACK FENCE] OTA end failed — rollback retained on active slot.");
    return false;
  }

  auto *partition = static_cast<const esp_partition_t *>(updatePartition_);
  if (esp_ota_set_boot_partition(partition) != ESP_OK) {
    Serial.println("[ROLLBACK FENCE] Boot partition swap rejected.");
    return false;
  }

  Serial.println(
      "[SUCCESS] Boot pointer swapped atomically. Hard resetting on safe clock edge...");
  esp_restart();
  return true;
#else
  return false;
#endif
}
