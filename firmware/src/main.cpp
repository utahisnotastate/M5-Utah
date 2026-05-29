#include <Arduino.h>
#include <M5Unified.h>
#include <ArduinoJson.h>

#include "registry_runtime.h"

static constexpr uint32_t BAUDRATE = 115200;
static constexpr size_t MAX_PAYLOAD = 4096;

namespace {

void resolveDisplayIntent(const JsonObjectConst &display) {
  if (display["clear"] | false) {
    uint16_t bg = display["bg_color"] | 0x0000;
    M5.Display.fillScreen(bg);
  }

  if (display.containsKey("text")) {
    JsonObjectConst text = display["text"].as<JsonObjectConst>();
    const int x = text["x"] | 0;
    const int y = text["y"] | 0;
    const int size = text["size"] | 2;
    const uint16_t color = text["color"] | 0xFFFF;
    const char *payload = text["payload"] | "";

    M5.Display.setTextSize(size);
    M5.Display.setTextColor(color);
    M5.Display.drawString(payload, x, y);
  }
}

void resolveSpeakerIntent(const JsonObjectConst &speaker) {
  if (speaker.containsKey("tone")) {
    JsonObjectConst tone = speaker["tone"].as<JsonObjectConst>();
    const double frequency = tone["frequency"] | 440.0;
    const int duration = tone["duration"] | 50;
    const int channel = tone["channel"] | 0;
    M5.Speaker.tone(frequency, duration, channel);
    return;
  }

  if (speaker["stop"] | false) {
    M5.Speaker.stop();
  }
}

void resolvePowerIntent(const JsonObjectConst &power) {
  if (power.containsKey("led")) {
    uint8_t brightness = power["led"] | 0;
    M5.Power.setLed(brightness);
  }

  if (power["off"] | false) {
    M5.Power.powerOff();
  }
}

void sendAck(bool ok, const char *error = "", JsonObjectConst extra = JsonObjectConst()) {
  StaticJsonDocument<512> doc;
  doc["type"] = "ack";
  doc["ok"] = ok;
  if (!ok) {
    doc["error"] = error;
  }
  if (!extra.isNull()) {
    doc["capabilities"] = extra["capabilities"];
  }
  serializeJson(doc, Serial);
  Serial.println();
}

void emitTelemetry() {
  StaticJsonDocument<768> doc;
  doc["type"] = "telemetry";
  doc["status"] = (ESP.getFreeHeap() < 20000) ? "degraded" : "operational";
  doc["board_id"] = static_cast<int>(M5.getBoard());
  doc["ts_us"] = micros();
  doc["battery_pct"] = M5.Power.getBatteryLevel();
  doc["charging"] = static_cast<int>(M5.Power.isCharging());

  JsonObject metrics = doc["metrics"].to<JsonObject>();
  metrics["free_heap"] = ESP.getFreeHeap();
  metrics["latency_budget_ms"] = 50;
  metrics["i2c_bandwidth_pct"] = 35;

  if (M5.Imu.isEnabled()) {
    M5.Imu.update();
    auto data = M5.Imu.getImuData();
    JsonObject accel = doc["accel"].to<JsonObject>();
    accel["x"] = data.accel.x;
    accel["y"] = data.accel.y;
    accel["z"] = data.accel.z;
  }

  serializeJson(doc, Serial);
  Serial.println();
}

}  // namespace

void setup() {
  auto cfg = M5.config();
  cfg.serial_baudrate = BAUDRATE;
  cfg.clear_display = true;
  cfg.internal_imu = true;
  cfg.internal_rtc = true;
  cfg.internal_spk = true;
  M5.begin(cfg);

  M5.Display.setRotation(1);
  M5.Display.setTextSize(2);
  M5.Display.println("M5 Resolver Online");

  M5.Speaker.setVolume(64);
  M5.Speaker.tone(880, 60);

  registryRuntimeInit();
}

void loop() {
  M5.update();
  registrySupervisorTick();

  if (Serial.available() > 0) {
    String payload = Serial.readStringUntil('\n');
    if (payload.length() > MAX_PAYLOAD) {
      sendAck(false, "payload_too_large");
      return;
    }

    StaticJsonDocument<MAX_PAYLOAD> doc;
    auto err = deserializeJson(doc, payload);
    if (err) {
      sendAck(false, err.c_str());
      return;
    }

    JsonObjectConst root = doc.as<JsonObjectConst>();

    if (root["capability_query"] | false) {
      StaticJsonDocument<256> capsDoc;
      JsonObject capsObj = capsDoc.to<JsonObject>();
      registryRespondCapabilities(capsObj);
      StaticJsonDocument<384> ackDoc;
      ackDoc["type"] = "ack";
      ackDoc["ok"] = true;
      ackDoc["capabilities"] = capsObj["capabilities"];
      serializeJson(ackDoc, Serial);
      Serial.println();
      return;
    }

    if (root.containsKey("registry")) {
      registryHotReload(root["registry"].as<JsonObjectConst>());
      sendAck(true);
      return;
    }

    if (root.containsKey("display")) {
      resolveDisplayIntent(root["display"].as<JsonObjectConst>());
    }
    if (root.containsKey("speaker")) {
      resolveSpeakerIntent(root["speaker"].as<JsonObjectConst>());
    }
    if (root.containsKey("power")) {
      resolvePowerIntent(root["power"].as<JsonObjectConst>());
    }

    sendAck(true);
  }

  static uint32_t lastTelemetryMs = 0;
  uint32_t now = millis();
  if (now - lastTelemetryMs >= 50) {
    emitTelemetry();
    lastTelemetryMs = now;
  }

  delay(2);
}
