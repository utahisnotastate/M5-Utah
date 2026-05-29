#pragma once

#include <freertos/FreeRTOS.h>
#include <freertos/task.h>

#include "StateForker.h"

constexpr size_t kSandboxStackWords = 256;
constexpr UBaseType_t kSandboxStackHighWaterMin = 100;

void sandboxedUnitWorker(void *param);

bool spawnSandboxedUnit(const char *name, UnitTaskConfig *cfg, UBaseType_t priority, TaskHandle_t *outHandle);

void sandboxReleaseHandle(TaskHandle_t handle);
