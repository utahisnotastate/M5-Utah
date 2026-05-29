#pragma once

#include <stdint.h>

#include <freertos/FreeRTOS.h>
#include <freertos/task.h>

struct UnitTaskConfig {
  char name[32];
  char semantic[48];
  int frequencyHz;
  int priority;
  bool active;
  uint32_t sequenceId;
  int allocationHandleId;
  int bufferSizeBytes;
  int assignedPriorityTier;
};

enum UnitExecutionState {
  UNIT_STAGED = 0,
  UNIT_RUNNING = 1,
  UNIT_DEGRADED = 2,
  UNIT_TERMINATED = 3
};

class StateForker {
 public:
  static StateForker &instance();

  bool stageAndForkUnit(const char *unitName, UnitTaskConfig *cfg, uint32_t seqId,
                        TaskFunction_t worker);
  void terminateUnit(const char *unitName);
  void terminateUnitsNotInList(const char *const *keepNames, int keepCount);
  void resetAll();
  int activeCount() const;

 private:
  StateForker() = default;

  struct ForkedUnit {
    char name[32];
    UnitExecutionState state;
    TaskHandle_t executionHandle;
    uint32_t activeSequenceId;
    UnitTaskConfig config;
  };

  static constexpr int kMaxPool = 10;
  ForkedUnit pool_[kMaxPool];
  UnitTaskConfig shadowCfg_[kMaxPool];
  int trackingCount_ = 0;

  int findIndex(const char *unitName) const;
  bool spawnNewUnit(ForkedUnit *slot, UnitTaskConfig *cfg, uint32_t seqId, TaskFunction_t worker);
  bool hotSwapUnit(ForkedUnit *slot, UnitTaskConfig *cfg, uint32_t seqId, TaskFunction_t worker);
};

void unitWorker(void *param);
