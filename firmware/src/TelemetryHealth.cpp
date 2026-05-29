#include "TelemetryHealth.h"

#include "M5Kernel.h"

#include <Arduino.h>

namespace {

uint8_t g_activeUnitId = 0;
uint8_t g_activePin = 0;
uint32_t g_lastOrchestrationTicks = 0;
uint32_t g_lastJitterMs = 0;

}  // namespace

void telemetryHealthRecordFastPath(uint8_t unitId, uint8_t pin) {
  g_activeUnitId = unitId;
  g_activePin = pin;
}

uint8_t telemetryHealthActiveUnit() { return g_activeUnitId; }

uint8_t telemetryHealthActivePin() { return g_activePin; }

uint32_t telemetryHealthLastLoopJitterMs() { return g_lastJitterMs; }

void telemetryHealthUpdateOrchestrationJitter() {
  const uint32_t ticks = M5Kernel::orchestrationTicks();
  if (g_lastOrchestrationTicks > 0 && ticks > g_lastOrchestrationTicks) {
    const uint32_t delta = ticks - g_lastOrchestrationTicks;
    g_lastJitterMs = delta > 5 ? (delta - 2) * 2 : 0;
  }
  g_lastOrchestrationTicks = ticks;
}
