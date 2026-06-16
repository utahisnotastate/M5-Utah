#include "ImmortalDiscovery.h"

#include <Arduino.h>
#include <ArduinoJson.h>
#include <Wire.h>

#include <freertos/FreeRTOS.h>
#include <freertos/task.h>

namespace {

constexpr uint32_t kDiscoveryPollIntervalMs = 500;
constexpr uint32_t kDiscoveryTaskStack = 4096;
constexpr UBaseType_t kDiscoveryTaskPriority = 1;

#if defined(ARDUINO_M5STACK_CORES3) || defined(CONFIG_IDF_TARGET_ESP32S3)
constexpr int kPortASdaPin = 2;
constexpr int kPortASclPin = 1;
#else
constexpr int kPortASdaPin = 21;
constexpr int kPortASclPin = 22;
#endif

bool g_discoveryActive = false;
bool g_activeAddresses[128] = {false};

const char *lookupUnitForAddress(uint8_t address) {
  switch (address) {
    case 0x44:
    case 0x70:
      return "ENV_III_SENSOR";
    case 0x68:
      return "MPU6886_IMU";
    case 0x41:
      return "VL53L1X_TOF";
    case 0x76:
    case 0x77:
      return "BMP280_ENV";
    default:
      return "UNKNOWN_SILICON";
  }
}

void emitDiscoveryEvent(const char *event, uint8_t address) {
  StaticJsonDocument<256> doc;
  doc["event"] = event;
  doc["port"] = "A";
  doc["hex_address"] = address;
  char hexBuf[5];
  snprintf(hexBuf, sizeof(hexBuf), "0x%02X", address);
  doc["hex_address_str"] = hexBuf;
  doc["unit"] = lookupUnitForAddress(address);
  serializeJson(doc, Serial);
  Serial.println();
}

void i2cScannerTask(void *param) {
  (void)param;
  Serial.println("[IMMORTAL] Autonomic I2C discovery task active on Core 0.");

  for (;;) {
    for (uint8_t address = 1; address < 127; address++) {
      Wire.beginTransmission(address);
      const uint8_t error = Wire.endTransmission();

      if (error == 0) {
        if (!g_activeAddresses[address]) {
          g_activeAddresses[address] = true;
          emitDiscoveryEvent("discovery", address);
        }
      } else if (g_activeAddresses[address]) {
        g_activeAddresses[address] = false;
        emitDiscoveryEvent("disconnect", address);
      }
    }
    vTaskDelay(pdMS_TO_TICKS(kDiscoveryPollIntervalMs));
  }
}

}  // namespace

void immortalDiscoveryInit() {
  if (g_discoveryActive) {
    return;
  }

  Wire.begin(kPortASdaPin, kPortASclPin, 100000);

  const BaseType_t created = xTaskCreatePinnedToCore(
      i2cScannerTask, "I2C_Discovery", kDiscoveryTaskStack, nullptr, kDiscoveryTaskPriority,
      nullptr, 0);

  if (created == pdPASS) {
    g_discoveryActive = true;
    Serial.println("[IMMORTAL] Grove Port A stochastic I2C polling armed (500ms).");
  } else {
    Serial.println("[IMMORTAL] Failed to start I2C discovery task.");
  }
}

bool immortalDiscoveryIsActive() { return g_discoveryActive; }
