#include "M5Kernel.h"

#include "BusArbitrator.h"
#include "CrossCorePipe.h"
#include "DualCoreHarness.h"
#include "HandleMemory.h"
#include "OmegaDefense.h"
#include "PriorityGatekeeper.h"
#include "ResourceOrchestrator.h"
#include "StochasticShield.h"
#include "SystemHealthHarvester.h"
#include "TelemetryHealth.h"
#include "VirtualEventGrid.h"
#include "TimeTravelJournal.h"
#include "registry_runtime.h"

#include <Arduino.h>
#include <ArduinoJson.h>
#include <M5Unified.h>
#include <freertos/FreeRTOS.h>
#include <freertos/task.h>

#include <cstring>

extern bool processInboundJsonPayload(char *payload, size_t len);
extern bool processInboundBinaryPayload(const uint8_t *data, size_t len, bool &ok);
extern void sendTransportAck(bool ok, const char *error);
extern void emitTelemetry();
extern void emitHardwareEvent(const char *eventType, JsonObjectConst metadata);

namespace {

constexpr uint32_t kApplicationTaskStack = 8192;
constexpr UBaseType_t kApplicationTaskPriority = 2;
constexpr uint32_t kTelemetryIntervalMs = 50;

TaskHandle_t g_applicationCoreTaskHandle = nullptr;
bool g_kernelRunning = false;
uint32_t g_processedFrameCount = 0;
uint32_t g_orchestrationTicks = 0;

struct JsonDispatchContext {
  char *payload;
  size_t length;
};

void jsonDispatchBody(void *context) {
  auto *ctx = static_cast<JsonDispatchContext *>(context);
  if (ctx != nullptr && ctx->payload != nullptr) {
    processInboundJsonPayload(ctx->payload, ctx->length);
  }
}

void jsonDispatchTrampoline(void *context) {
  StochasticShield::executeWithBrownianJitter(jsonDispatchBody, context);
}

bool payloadReferencesRegistry(const char *payload, size_t length) {
  if (payload == nullptr || length < 12) {
    return false;
  }
  static const char kRegistryKey[] = "\"registry\"";
  for (size_t i = 0; i + sizeof(kRegistryKey) - 1 <= length; i++) {
    if (memcmp(payload + i, kRegistryKey, sizeof(kRegistryKey) - 1) == 0) {
      return true;
    }
  }
  return false;
}

void applicationCoreLoop(void *param) {
  (void)param;
  Serial.println("[CORE 1] Isolated application execution kernel active (Feature 52).");

  static uint32_t lastTelemetryMs = 0;
  static bool prevBtnA = false;

  for (;;) {
    g_orchestrationTicks++;
    telemetryHealthUpdateOrchestrationJitter();
    const uint32_t freeHeap = ESP.getFreeHeap();
    globalResourceOrchestrator().orchestrateTick(freeHeap);
    M5.update();
    registrySupervisorTick();
    omegaDefenseTick(g_orchestrationTicks, g_processedFrameCount);

    while (M5Kernel::dispatchPipeFrame(0, nullptr, 0)) {
    }

    const uint32_t now = millis();

    const bool btnA = M5.BtnA.isPressed();
    if (btnA && !prevBtnA) {
      StaticJsonDocument<128> meta;
      JsonObject obj = meta.to<JsonObject>();
      obj["hardware_source_pin"] = 39;
      obj["state"] = "FALLING";
      emitHardwareEvent("button_click_event", static_cast<JsonObjectConst>(obj));
    }
    prevBtnA = btnA;

    scanFilteredImuVirtualEvents();

    if (now - lastTelemetryMs >= kTelemetryIntervalMs) {
      emitTelemetry();
      lastTelemetryMs = now;
    }

    globalHealthHarvester().streamSystemVitals(telemetryHealthActiveUnit());

    vTaskDelay(pdMS_TO_TICKS(2));
  }
}

}  // namespace

void m5KernelApplicationCoreTask(void *param) { applicationCoreLoop(param); }

bool M5Kernel::dispatchPipeFrame(uint8_t kind, uint8_t *payload, size_t payloadLen) {
  if (kind == 0 && payload == nullptr) {
    size_t frameSize = 0;
    void *item = globalCorePipe().receiveActiveFramePointer(&frameSize);
    if (item == nullptr || frameSize < 2) {
      if (item != nullptr) {
        globalCorePipe().releaseProcessedFrame(item);
      }
      return false;
    }

    auto *bytes = static_cast<uint8_t *>(item);
    kind = bytes[0];
    payload = bytes + 1;
    payloadLen = frameSize - 1;

    const bool handled = dispatchPipeFrame(kind, payload, payloadLen);
    globalCorePipe().releaseProcessedFrame(item);
    if (handled) {
      g_processedFrameCount++;
    }
    return handled;
  }

  if (kind == kPipeFrameJson) {
    char *json = reinterpret_cast<char *>(payload);
    const bool isRegistry = payloadReferencesRegistry(json, payloadLen);
    const bool isNonCritical = jsonPayloadIsNonCritical(json, payloadLen);
    if (!globalResourceOrchestrator().allowIntentDispatch(isRegistry, false) &&
        isNonCritical) {
      globalResourceOrchestrator().recordDeferredFrame();
      sendTransportAck(false, "orchestrator_deferred_non_critical");
      return true;
    }
    if (isRegistry) {
      const int handleId = globalMemoryManager().allocateHandle(payloadLen + 1);
      if (handleId >= 0) {
        uint8_t *destinationBuffer = globalMemoryManager().resolveHandle(handleId);
        if (destinationBuffer != nullptr) {
          memcpy(destinationBuffer, payload, payloadLen);
          destinationBuffer[payloadLen] = '\0';
          JsonDispatchContext ctx{reinterpret_cast<char *>(destinationBuffer), payloadLen};
          globalGatekeeper().executePrioritizedAccessWithContext(
              kGateLockRegistry, 0, uxTaskPriorityGet(nullptr), jsonDispatchTrampoline, &ctx);
          globalMemoryManager().releaseHandle(handleId);
          return true;
        }
        globalMemoryManager().releaseHandle(handleId);
      }
    }
    return processInboundJsonPayload(json, payloadLen);
  }

  if (kind == kPipeFrameBinary) {
    if (!globalResourceOrchestrator().allowIntentDispatch(false, true)) {
      globalResourceOrchestrator().recordDeferredFrame();
      sendTransportAck(false, "orchestrator_deferred_binary");
      return true;
    }
    bool ok = false;
    const bool handled = processInboundBinaryPayload(payload, payloadLen, ok);
    sendTransportAck(ok, handled && !ok ? "binary_transport_rejected" : "");
    return handled;
  }

  return false;
}

void M5Kernel::start() {
  if (g_kernelRunning) {
    return;
  }

  Serial.println("[INTEGRATION INIT] Activating m5-utah SOTA runtime kernel...");

  globalResourceOrchestrator().initialize();
  globalCorePipe().initializeBufferPipe();
  startProtocolCoreIngestTask();

  xTaskCreatePinnedToCore(m5KernelApplicationCoreTask, "m5_app_engine", kApplicationTaskStack,
                          nullptr, kApplicationTaskPriority, &g_applicationCoreTaskHandle,
                          kM5KernelCoreApplication);

  g_kernelRunning = true;
  timeTravelRecord("kernel:start");
  Serial.println("[M5-KERNEL] Dual-core non-blocking harness active (Core 0 ingest / Core 1 exec).");
}

void M5Kernel::shutdown() {
  if (g_applicationCoreTaskHandle != nullptr) {
    vTaskDelete(g_applicationCoreTaskHandle);
    g_applicationCoreTaskHandle = nullptr;
  }
  g_kernelRunning = false;
}

bool M5Kernel::isRunning() { return g_kernelRunning; }

uint32_t M5Kernel::processedFrameCount() { return g_processedFrameCount; }

uint32_t M5Kernel::orchestrationTicks() { return g_orchestrationTicks; }

bool m5KernelDrainPipeFrame() { return M5Kernel::dispatchPipeFrame(0, nullptr, 0); }
