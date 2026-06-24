#include "Sandbox.h"

#include "TimeTravelJournal.h"
#include "registry_runtime.h"

#include <Arduino.h>
#include <M5Unified.h>
#include <cstring>

namespace {

constexpr int kMaxSandboxSlots = 4;
constexpr uint32_t kMinFreeHeap = 20000;

struct SandboxSlot {
  StackType_t stack[kSandboxStackWords];
  StaticTask_t taskBuffer;
  TaskHandle_t handle;
  bool inUse;
};

SandboxSlot g_slots[kMaxSandboxSlots];

void executeSemantic(const char *action) {
  if (strcmp(action, "ACTION_INDICATE_STATUS_SUCCESS") == 0) {
    M5.Display.fillScreen(TFT_BLACK);
    M5.Display.setTextColor(TFT_GREEN);
    M5.Display.drawString("OK", 10, 10);
    M5.Speaker.tone(880, 40);
    return;
  }
  if (strcmp(action, "ACTION_INDICATE_STATUS_ERROR") == 0) {
    M5.Display.fillScreen(TFT_BLACK);
    M5.Display.setTextColor(TFT_RED);
    M5.Display.drawString("ERR", 10, 10);
    M5.Speaker.tone(220, 80);
    return;
  }
  if (strcmp(action, "ACTION_INDICATE_ALERT") == 0) {
    M5.Speaker.tone(1200, 60);
    return;
  }
  if (strcmp(action, "ACTION_REACT_TO_MOTION") == 0) {
    if (M5.Imu.isEnabled()) {
      M5.Imu.update();
      auto data = M5.Imu.getImuData();
      if (abs(data.accel.x) > 0.35f) {
        M5.Speaker.tone(660, 30);
      }
    }
  }
}

SandboxSlot *acquireSlot() {
  for (int i = 0; i < kMaxSandboxSlots; ++i) {
    if (!g_slots[i].inUse) {
      g_slots[i].inUse = true;
      g_slots[i].handle = nullptr;
      return &g_slots[i];
    }
  }
  return nullptr;
}

SandboxSlot *findSlotByHandle(TaskHandle_t handle) {
  for (int i = 0; i < kMaxSandboxSlots; ++i) {
    if (g_slots[i].inUse && g_slots[i].handle == handle) {
      return &g_slots[i];
    }
  }
  return nullptr;
}

}  // namespace

void sandboxedUnitWorker(void *param) {
  UnitTaskConfig *cfg = static_cast<UnitTaskConfig *>(param);
  if (cfg == nullptr) {
    vTaskDelete(nullptr);
    return;
  }
  Serial.printf("[SANDBOX] Memory boundary active for unit %s\n", cfg->name);

  const uint32_t intervalMs = cfg->frequencyHz > 0 ? (1000 / cfg->frequencyHz) : 1000;

  for (;;) {
    UBaseType_t highWaterMark = uxTaskGetStackHighWaterMark(nullptr);
    if (highWaterMark < kSandboxStackHighWaterMin) {
      Serial.println(
          "[CRITICAL MEMORY VIOLATION DETECTED] Sandboxed memory exhaustion imminent! "
          "Tearing down execution thread instantly.");
      timeTravelRecord("sandbox:violation");
      registryRevertUnitToStable(cfg->name);
      vTaskDelete(nullptr);
    }

    if (ESP.getFreeHeap() < kMinFreeHeap) {
      vTaskDelay(pdMS_TO_TICKS(1000));
      continue;
    }

    if (cfg->active && cfg->semantic[0] != '\0') {
      executeSemantic(cfg->semantic);
    }
    vTaskDelay(pdMS_TO_TICKS(intervalMs));
  }
}

bool spawnSandboxedUnit(const char *name, UnitTaskConfig *cfg, UBaseType_t priority,
                        TaskHandle_t *outHandle) {
  SandboxSlot *slot = acquireSlot();
  if (slot == nullptr) {
    return false;
  }

  slot->handle = xTaskCreateStaticPinnedToCore(
      sandboxedUnitWorker, name, kSandboxStackWords, cfg, priority, slot->stack, &slot->taskBuffer,
      1);

  if (slot->handle == nullptr) {
    slot->inUse = false;
    return false;
  }

  *outHandle = slot->handle;
  return true;
}

void sandboxReleaseHandle(TaskHandle_t handle) {
  SandboxSlot *slot = findSlotByHandle(handle);
  if (slot != nullptr) {
    slot->inUse = false;
    slot->handle = nullptr;
  }
}
