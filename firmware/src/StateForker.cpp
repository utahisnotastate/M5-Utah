#include "StateForker.h"

#include "Sandbox.h"
#include "SpeculativeStaging.h"

#include <Arduino.h>
#include <cstring>

StateForker &StateForker::instance() {
  static StateForker fork;
  return fork;
}

void unitWorker(void *param) { sandboxedUnitWorker(param); }

int StateForker::findIndex(const char *unitName) const {
  for (int i = 0; i < trackingCount_; ++i) {
    if (strcmp(pool_[i].name, unitName) == 0) {
      return i;
    }
  }
  return -1;
}

bool StateForker::spawnNewUnit(ForkedUnit *slot, UnitTaskConfig *cfg, uint32_t seqId,
                               TaskFunction_t worker) {
  memcpy(&slot->config, cfg, sizeof(UnitTaskConfig));
  slot->config.sequenceId = seqId;
  strncpy(slot->name, cfg->name, sizeof(slot->name) - 1);
  slot->activeSequenceId = seqId;
  slot->state = UNIT_RUNNING;

  TaskHandle_t handle = nullptr;
  if (!speculativeSpawnUnit(slot->name, &slot->config, worker, cfg->priority, &handle)) {
    return false;
  }
  slot->executionHandle = handle;
  return true;
}

bool StateForker::hotSwapUnit(ForkedUnit *slot, UnitTaskConfig *cfg, uint32_t seqId,
                              TaskFunction_t worker) {
  Serial.printf("[FORKER] Hot-shadow swap for %s (seq %u)\n", slot->name, seqId);

  int slotIndex = static_cast<int>(slot - pool_);
  if (slotIndex < 0 || slotIndex >= kMaxPool) {
    return false;
  }

  UnitTaskConfig *shadowCfg = &shadowCfg_[slotIndex];
  memcpy(shadowCfg, cfg, sizeof(UnitTaskConfig));
  shadowCfg->sequenceId = seqId;

  TaskHandle_t shadowHandle = nullptr;
  if (!speculativeSpawnUnit("shadow_unit", shadowCfg, worker, cfg->priority + 2, &shadowHandle)) {
    slot->state = UNIT_DEGRADED;
    return false;
  }

  if (slot->executionHandle != nullptr) {
    vTaskPrioritySet(slot->executionHandle, 1);
    vTaskDelay(pdMS_TO_TICKS(10));
    sandboxReleaseHandle(slot->executionHandle);
    vTaskDelete(slot->executionHandle);
  }

  memcpy(&slot->config, shadowCfg, sizeof(UnitTaskConfig));
  slot->executionHandle = shadowHandle;
  vTaskPrioritySet(shadowHandle, cfg->priority + 1);
  slot->activeSequenceId = seqId;
  slot->state = UNIT_RUNNING;
  return true;
}

bool StateForker::stageAndForkUnit(const char *unitName, UnitTaskConfig *cfg, uint32_t seqId,
                                   TaskFunction_t worker) {
  Serial.printf("[FORKER] Staging %s (seq %u)\n", unitName, seqId);

  int idx = findIndex(unitName);
  if (idx >= 0 && pool_[idx].state == UNIT_RUNNING) {
    return hotSwapUnit(&pool_[idx], cfg, seqId, worker);
  }

  if (trackingCount_ >= kMaxPool) {
    return false;
  }

  ForkedUnit *slot = &pool_[trackingCount_];
  if (spawnNewUnit(slot, cfg, seqId, worker)) {
    trackingCount_++;
    return true;
  }
  return false;
}

void StateForker::terminateUnit(const char *unitName) {
  int idx = findIndex(unitName);
  if (idx < 0) return;

  ForkedUnit *slot = &pool_[idx];
  slot->state = UNIT_TERMINATED;
  if (slot->executionHandle != nullptr) {
    vTaskPrioritySet(slot->executionHandle, 1);
    vTaskDelay(pdMS_TO_TICKS(10));
    sandboxReleaseHandle(slot->executionHandle);
    vTaskDelete(slot->executionHandle);
    slot->executionHandle = nullptr;
  }

  for (int i = idx; i < trackingCount_ - 1; ++i) {
    pool_[i] = pool_[i + 1];
  }
  trackingCount_--;
}

void StateForker::terminateUnitsNotInList(const char *const *keepNames, int keepCount) {
  for (int i = trackingCount_ - 1; i >= 0; --i) {
    bool keep = false;
    for (int j = 0; j < keepCount; ++j) {
      if (strcmp(pool_[i].name, keepNames[j]) == 0) {
        keep = true;
        break;
      }
    }
    if (!keep) {
      terminateUnit(pool_[i].name);
    }
  }
}

void StateForker::resetAll() {
  for (int i = trackingCount_ - 1; i >= 0; --i) {
    if (pool_[i].executionHandle != nullptr) {
      sandboxReleaseHandle(pool_[i].executionHandle);
      vTaskDelete(pool_[i].executionHandle);
      pool_[i].executionHandle = nullptr;
    }
  }
  trackingCount_ = 0;
}

int StateForker::activeCount() const { return trackingCount_; }
