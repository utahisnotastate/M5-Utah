#pragma once

#include <ArduinoJson.h>
#include <freertos/FreeRTOS.h>
#include <freertos/semphr.h>
#include <freertos/task.h>
#include <stdint.h>

struct GuardedAsset {
  const char *assetName;
  SemaphoreHandle_t mutexHandle;
  int primaryOwnerUnitId;
  UBaseType_t defaultWorkerPriority;
  bool active;
};

using GatekeeperActionFn = void (*)(void *context);

constexpr int kMaxGuardedAssets = 4;

constexpr int kGateLockI2cBus = 0;
constexpr int kGateLockSpiBus = 1;
constexpr int kGateLockRegistry = 2;
constexpr int kGateLockCrypto = 3;

class PriorityGatekeeper {
 public:
  void initializeGatekeeper();
  int registerGuardedAsset(const char *name, UBaseType_t criticalPriority);
  bool executePrioritizedAccess(int lockId, int unitId, UBaseType_t callingTaskPriority,
                                void (*criticalSection)(void));
  bool executePrioritizedAccessWithContext(int lockId, int unitId, UBaseType_t callingTaskPriority,
                                           GatekeeperActionFn action, void *context);
  UBaseType_t tierToPriority(int assignedPriorityTier) const;
  int activeLockCount() const;
  uint32_t proactiveBoostCount() const;

 private:
  GuardedAsset registryLocks_[kMaxGuardedAssets] = {};
  int lockCount_ = 0;
  uint32_t boostCount_ = 0;
};

PriorityGatekeeper &globalGatekeeper();

int priorityTierFromUnit(JsonObjectConst unit);
