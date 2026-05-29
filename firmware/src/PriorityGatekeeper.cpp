#include "PriorityGatekeeper.h"

#include "TimeTravelJournal.h"

#include <Arduino.h>
#include <ArduinoJson.h>

PriorityGatekeeper &globalGatekeeper() {
  static PriorityGatekeeper gatekeeper;
  return gatekeeper;
}

void PriorityGatekeeper::initializeGatekeeper() {
  lockCount_ = 0;
  boostCount_ = 0;
  for (int i = 0; i < kMaxGuardedAssets; i++) {
    registryLocks_[i].assetName = nullptr;
    registryLocks_[i].mutexHandle = nullptr;
    registryLocks_[i].primaryOwnerUnitId = -1;
    registryLocks_[i].defaultWorkerPriority = 1;
    registryLocks_[i].active = false;
  }

  registerGuardedAsset("i2c_bus", 5);
  registerGuardedAsset("spi_bus", 5);
  registerGuardedAsset("registry_flash", 4);
  registerGuardedAsset("crypto_block", 6);

  Serial.println("[GATEKEEPER] Predictive real-time scheduling barrier operational.");
}

int PriorityGatekeeper::registerGuardedAsset(const char *name, UBaseType_t criticalPriority) {
  if (lockCount_ >= kMaxGuardedAssets || name == nullptr) {
    return -1;
  }

  registryLocks_[lockCount_].assetName = name;
  registryLocks_[lockCount_].mutexHandle = xSemaphoreCreateMutex();
  registryLocks_[lockCount_].primaryOwnerUnitId = -1;
  registryLocks_[lockCount_].defaultWorkerPriority = criticalPriority;
  registryLocks_[lockCount_].active = registryLocks_[lockCount_].mutexHandle != nullptr;

  const int assigned = lockCount_;
  lockCount_++;
  return assigned;
}

UBaseType_t PriorityGatekeeper::tierToPriority(int assignedPriorityTier) const {
  if (assignedPriorityTier >= 3) {
    return 6;
  }
  if (assignedPriorityTier == 2) {
    return 4;
  }
  return 2;
}

bool PriorityGatekeeper::executePrioritizedAccessWithContext(int lockId, int unitId,
                                                             UBaseType_t callingTaskPriority,
                                                             GatekeeperActionFn action,
                                                             void *context) {
  if (action == nullptr || lockId < 0 || lockId >= lockCount_ ||
      !registryLocks_[lockId].active) {
    return false;
  }

  GuardedAsset &asset = registryLocks_[lockId];
  TaskHandle_t currentTaskHandle = xTaskGetCurrentTaskHandle();
  const UBaseType_t originalPriority = callingTaskPriority;

  if (callingTaskPriority < asset.defaultWorkerPriority) {
    Serial.printf(
        "[PROACTIVE BOOST] Elevating Unit Task %d to Priority %u to protect critical execution "
        "bounds.\n",
        unitId, static_cast<unsigned>(asset.defaultWorkerPriority));
    vTaskPrioritySet(currentTaskHandle, asset.defaultWorkerPriority);
    boostCount_++;
  }

  if (xSemaphoreTake(asset.mutexHandle, pdMS_TO_TICKS(100)) != pdTRUE) {
    vTaskPrioritySet(currentTaskHandle, originalPriority);
    return false;
  }

  asset.primaryOwnerUnitId = unitId;
  action(context);
  asset.primaryOwnerUnitId = -1;
  xSemaphoreGive(asset.mutexHandle);
  vTaskPrioritySet(currentTaskHandle, originalPriority);
  timeTravelRecord("gatekeeper:access");
  return true;
}

bool PriorityGatekeeper::executePrioritizedAccess(int lockId, int unitId,
                                                  UBaseType_t callingTaskPriority,
                                                  void (*criticalSection)(void)) {
  struct ThunkContext {
    void (*fn)(void);
  } ctx{criticalSection};

  return executePrioritizedAccessWithContext(
      lockId, unitId, callingTaskPriority,
      [](void *raw) {
        auto *thunk = static_cast<ThunkContext *>(raw);
        if (thunk != nullptr && thunk->fn != nullptr) {
          thunk->fn();
        }
      },
      &ctx);
}

int PriorityGatekeeper::activeLockCount() const { return lockCount_; }

uint32_t PriorityGatekeeper::proactiveBoostCount() const { return boostCount_; }

int priorityTierFromUnit(JsonObjectConst unit) {
  const int tier = unit["assigned_priority_tier"] | 0;
  if (tier > 0) {
    return tier;
  }
  if (unit["realtime_critical"] | false) {
    return 3;
  }
  return 1;
}
