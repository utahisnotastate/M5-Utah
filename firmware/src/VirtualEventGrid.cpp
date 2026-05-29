#include "VirtualEventGrid.h"

#include "VectorTelemetry.h"

#include <M5Unified.h>
#include <Arduino.h>

extern void emitHardwareEvent(const char *eventType, JsonObjectConst metadata);

namespace {

StochasticTelemetryFilter g_imuFilter(kImuFilterProcessVariance, kImuFilterMeasurementVariance);
uint32_t g_lastImuVirtualEventMs = 0;

}  // namespace

StochasticTelemetryFilter &imuStochasticFilter() { return g_imuFilter; }

void broadcastPristineEvent(const char *eventType, float filteredMagnitude, int sourcePin) {
  StaticJsonDocument<256> eventDoc;
  eventDoc["type"] = "hardware_event";
  eventDoc["event_type"] = eventType;

  JsonObject payload = eventDoc["payload"].to<JsonObject>();
  payload["pin_source"] = sourcePin;
  payload["magnitude"] = filteredMagnitude;

  vectorTelemetry().attachToEvent(eventDoc.as<JsonObject>());

  Serial.print("[VIRTUAL_EVENT_STREAM]:");
  serializeJson(eventDoc, Serial);
  Serial.println();
}

void scanFilteredImuVirtualEvents() {
  if (!M5.Imu.isEnabled()) {
    return;
  }

  const uint32_t now = millis();
  if (now - g_lastImuVirtualEventMs < 500) {
    return;
  }

  M5.Imu.update();
  auto data = M5.Imu.getImuData();
  const float rawMagnitude = max(abs(data.accel.x), max(abs(data.accel.y), abs(data.accel.z)));
  const float pristine = g_imuFilter.computeFilteredMetric(rawMagnitude);

  if (pristine <= kImuTiltEventThreshold) {
    return;
  }

  StaticJsonDocument<128> meta;
  JsonObject obj = meta.to<JsonObject>();
  obj["axis"] = abs(data.accel.x) > abs(data.accel.y) ? "x" : "y";
  obj["magnitude"] = pristine;
  obj["pin_source"] = 34;
  emitHardwareEvent("motion_spike_event", static_cast<JsonObjectConst>(obj));
  broadcastPristineEvent("imu_tilt_event", pristine, 34);
  g_lastImuVirtualEventMs = now;
}
