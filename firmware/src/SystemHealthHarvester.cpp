#include "SystemHealthHarvester.h"

#include "TelemetryHealth.h"

#include <Arduino.h>
#include <esp_heap_caps.h>

namespace {

SystemHealthHarvester g_vitalsHarvester;
uint32_t g_lastReportTimestampMs = 0;

void printHexByte(uint8_t value) {
  const char hex[] = "0123456789ABCDEF";
  Serial.print(hex[(value >> 4) & 0x0F]);
  Serial.print(hex[value & 0x0F]);
}

}  // namespace

void systemHealthHarvesterInit() { g_lastReportTimestampMs = 0; }

void SystemHealthHarvester::streamSystemVitals(uint8_t activeUnitId) {
  const uint32_t now = millis();
  if (now - g_lastReportTimestampMs < kHealthVitalsReportIntervalMs) {
    return;
  }
  g_lastReportTimestampMs = now;

  DiagnosticReportFrame report{};
  report.unitId = activeUnitId;
  report.remainingHeapBytes = ESP.getFreeHeap();
  report.measuredTaskJitterMs =
      static_cast<uint8_t>(min<uint32_t>(255, telemetryHealthLastLoopJitterMs()));

  Serial.print("[HEALTH_VITALS_STREAM]:");
  const uint8_t *raw = reinterpret_cast<const uint8_t *>(&report);
  for (size_t i = 0; i < sizeof(report); ++i) {
    printHexByte(raw[i]);
  }
  Serial.println();
}

SystemHealthHarvester &globalHealthHarvester() { return g_vitalsHarvester; }
