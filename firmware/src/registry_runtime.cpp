#include "registry_runtime.h"

#include <cstring>

#include <M5Unified.h>
#include <freertos/FreeRTOS.h>
#include <freertos/task.h>

namespace {

constexpr int kMaxUnits = 8;
constexpr uint32_t kMinFreeHeap = 20000;

struct UnitTaskConfig {
  char name[24];
  char semantic[48];
  int frequencyHz;
  int priority;
  bool active;
};

static UnitTaskConfig g_units[kMaxUnits];
static TaskHandle_t g_handles[kMaxUnits];
static int g_unitCount = 0;
static bool g_safeguard = false;

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

void unitWorker(void *param) {
  UnitTaskConfig *cfg = static_cast<UnitTaskConfig *>(param);
  const uint32_t intervalMs = cfg->frequencyHz > 0 ? (1000 / cfg->frequencyHz) : 1000;

  for (;;) {
    if (g_safeguard) {
      vTaskDelay(pdMS_TO_TICKS(1000));
      continue;
    }
    if (ESP.getFreeHeap() < kMinFreeHeap) {
      Serial.printf("[SUPERVISOR] throttling unit %s (low heap)\n", cfg->name);
      vTaskDelay(pdMS_TO_TICKS(1000));
      continue;
    }
    if (cfg->active && cfg->semantic[0] != '\0') {
      executeSemantic(cfg->semantic);
    }
    vTaskDelay(pdMS_TO_TICKS(intervalMs));
  }
}

void clearUnitTasks() {
  for (int i = 0; i < g_unitCount; ++i) {
    if (g_handles[i] != nullptr) {
      vTaskDelete(g_handles[i]);
      g_handles[i] = nullptr;
    }
  }
  g_unitCount = 0;
}

void addUnitFromObject(const char *unitId, JsonObjectConst unit) {
  if (g_unitCount >= kMaxUnits) return;

  UnitTaskConfig &cfg = g_units[g_unitCount];
  memset(&cfg, 0, sizeof(cfg));
  strncpy(cfg.name, unitId, sizeof(cfg.name) - 1);
  const char *semantic = unit["semantic_action"] | "ACTION_INDICATE_STATUS_SUCCESS";
  strncpy(cfg.semantic, semantic, sizeof(cfg.semantic) - 1);
  cfg.frequencyHz = unit["frequency_hz"] | 2;
  if (cfg.frequencyHz < 1) cfg.frequencyHz = 1;
  if (cfg.frequencyHz > 60) cfg.frequencyHz = 60;
  cfg.priority = unit["priority"] | 1;
  cfg.active = unit["state"] | true;

  if (unit["safeguard_activated"] | false) {
    g_safeguard = true;
  }

  xTaskCreatePinnedToCore(
      unitWorker,
      cfg.name,
      3072,
      &g_units[g_unitCount],
      cfg.priority,
      &g_handles[g_unitCount],
      1);

  g_unitCount++;
}

}  // namespace

void registryRuntimeInit() {
  StaticJsonDocument<256> doc;
  JsonObject unit = doc.to<JsonObject>();
  unit["frequency_hz"] = 2;
  unit["semantic_action"] = "ACTION_INDICATE_STATUS_SUCCESS";
  unit["priority"] = 1;
  clearUnitTasks();
  addUnitFromObject("heartbeat", unit);
}

void registryHotReload(const JsonObjectConst &registryRoot) {
  clearUnitTasks();
  g_safeguard = registryRoot["safeguard"] | false;

  JsonObjectConst units = registryRoot["units"].as<JsonObjectConst>();
  if (!units.isNull()) {
    for (JsonPairConst kv : units) {
      addUnitFromObject(kv.key().c_str(), kv.value().as<JsonObjectConst>());
    }
    return;
  }

  JsonArrayConst unitsArr = registryRoot["units"].as<JsonArrayConst>();
  if (!unitsArr.isNull()) {
    for (JsonObjectConst unit : unitsArr) {
      const char *unitId = unit["unit_id"] | "unit";
      addUnitFromObject(unitId, unit);
    }
  }
}

void registrySupervisorTick() {
  if (ESP.getFreeHeap() < kMinFreeHeap) {
    g_safeguard = true;
  }
}

void registryRespondCapabilities(JsonObject out) {
  JsonArray caps = out["capabilities"].to<JsonArray>();
  caps.add("display");
  caps.add("speaker");
  caps.add("power");
  caps.add("registry_hot_reload");
  caps.add("semantic_actions");
  if (M5.Imu.isEnabled()) caps.add("accel");
}
