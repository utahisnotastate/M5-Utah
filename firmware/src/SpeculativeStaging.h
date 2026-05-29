#pragma once

#include <freertos/FreeRTOS.h>
#include <freertos/task.h>

#include <stdint.h>

constexpr uint32_t kSpeculativeMinFreeHeap = 25000;
constexpr uint32_t kSpeculativeDefaultTimeoutMs = 200;

class SpeculativeStagingBuffer {
 public:
  static SpeculativeStagingBuffer &instance();

  bool testSpeculativeTask(TaskFunction_t shadowTaskCode, void *parameters,
                           uint32_t verificationTimeoutMs, UBaseType_t operationalPriority,
                           TaskHandle_t *promotedHandle);

  bool isShadowConfirmedStable() const;

 private:
  SpeculativeStagingBuffer() = default;

  bool shadowTaskConfirmedStable_ = false;
  TaskHandle_t shadowTaskHandle_ = nullptr;
};

SpeculativeStagingBuffer &stagingBuffer();

bool speculativeSpawnUnit(const char *name, void *cfg, TaskFunction_t worker,
                          UBaseType_t operationalPriority, TaskHandle_t *outHandle,
                          uint32_t verificationTimeoutMs = kSpeculativeDefaultTimeoutMs);
