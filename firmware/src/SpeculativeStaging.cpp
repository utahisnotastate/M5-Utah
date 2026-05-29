#include "SpeculativeStaging.h"

#include "Sandbox.h"
#include "TimeTravelJournal.h"

#include <Arduino.h>

SpeculativeStagingBuffer &SpeculativeStagingBuffer::instance() {
  static SpeculativeStagingBuffer buffer;
  return buffer;
}

SpeculativeStagingBuffer &stagingBuffer() { return SpeculativeStagingBuffer::instance(); }

bool SpeculativeStagingBuffer::isShadowConfirmedStable() const {
  return shadowTaskConfirmedStable_;
}

bool SpeculativeStagingBuffer::testSpeculativeTask(
    TaskFunction_t shadowTaskCode, void *parameters, uint32_t verificationTimeoutMs,
    UBaseType_t operationalPriority, TaskHandle_t *promotedHandle) {
  Serial.println("[STAGING] Initializing speculative shadow thread fence...");
  shadowTaskConfirmedStable_ = false;

  if (shadowTaskHandle_ != nullptr) {
    sandboxReleaseHandle(shadowTaskHandle_);
    vTaskDelete(shadowTaskHandle_);
    shadowTaskHandle_ = nullptr;
  }

  TaskHandle_t shadowHandle = nullptr;
  if (!spawnSandboxedUnit("speculative_shadow", static_cast<UnitTaskConfig *>(parameters), 4,
                          &shadowHandle)) {
    return false;
  }
  shadowTaskHandle_ = shadowHandle;

  const uint32_t startCheckTime = millis();
  while (millis() - startCheckTime < verificationTimeoutMs) {
    const uint32_t currentFreeHeap = ESP.getFreeHeap();
    if (currentFreeHeap < kSpeculativeMinFreeHeap) {
      Serial.println(
          "[STAGING FAILURE] Speculative execution caused a resource exception! "
          "Dropping shadow thread.");
      timeTravelRecord("staging:failure");
      sandboxReleaseHandle(shadowTaskHandle_);
      vTaskDelete(shadowTaskHandle_);
      shadowTaskHandle_ = nullptr;
      return false;
    }
    vTaskDelay(pdMS_TO_TICKS(50));
  }

  Serial.println(
      "[STAGING SUCCESS] Speculative task passed validation constraints. "
      "Promoting to active system loop.");
  vTaskPrioritySet(shadowTaskHandle_, operationalPriority);
  shadowTaskConfirmedStable_ = true;
  timeTravelRecord("staging:success");

  if (promotedHandle != nullptr) {
    *promotedHandle = shadowTaskHandle_;
  }
  return true;
}

bool speculativeSpawnUnit(const char *name, void *cfg, TaskFunction_t worker,
                          UBaseType_t operationalPriority, TaskHandle_t *outHandle,
                          uint32_t verificationTimeoutMs) {
  (void)name;
  return stagingBuffer().testSpeculativeTask(worker, cfg, verificationTimeoutMs,
                                             operationalPriority, outHandle);
}
