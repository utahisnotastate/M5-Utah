#include "DynamicMultiplexer.h"

#include <SPI.h>
#include <Wire.h>

namespace {

bool g_i2cActive = false;
int g_i2cSda = -1;
int g_i2cScl = -1;

void logBus(const char *msg) {
  Serial.print("[MULTIPLEXER] ");
  Serial.println(msg);
}

}  // namespace

void DynamicMultiplexer::resetAll() {
  if (g_i2cActive) {
    Wire.end();
    g_i2cActive = false;
    g_i2cSda = -1;
    g_i2cScl = -1;
  }
}

void DynamicMultiplexer::configureProcessorTopology(JsonObjectConst unit) {
  const char *protocolType = unit["type"] | unit["bus_type"] | "raw_gpio";
  JsonArrayConst pins = unit["pins"].as<JsonArrayConst>();

  if (strcmp(protocolType, "I2C") == 0 || strcmp(protocolType, "i2c") == 0) {
    int sda = pins.size() > 0 ? pins[0].as<int>() : (unit["sda"] | -1);
    int scl = pins.size() > 1 ? pins[1].as<int>() : (unit["scl"] | -1);
    uint32_t frequency = unit["frequency_hz"] | unit["i2c_frequency"] | 100000;

    if (sda == -1 || scl == -1) {
      logBus("I2C config skipped: missing SDA/SCL");
      return;
    }
    if (sda == scl) {
      logBus("I2C config rejected: pin conflict");
      return;
    }

    Serial.printf("[MULTIPLEXER] Hot-swap I2C SDA=%d SCL=%d @ %u Hz\n", sda, scl, frequency);
    Wire.end();
    Wire.begin(sda, scl, frequency);
    g_i2cActive = true;
    g_i2cSda = sda;
    g_i2cScl = scl;
    return;
  }

  if (strcmp(protocolType, "SPI") == 0 || strcmp(protocolType, "spi") == 0) {
    int mosi = pins.size() > 0 ? pins[0].as<int>() : -1;
    int miso = pins.size() > 1 ? pins[1].as<int>() : -1;
    int sclk = pins.size() > 2 ? pins[2].as<int>() : -1;
    int cs = pins.size() > 3 ? pins[3].as<int>() : -1;

    if (mosi == -1 || sclk == -1) {
      logBus("SPI config skipped: need MOSI and SCLK");
      return;
    }

    Serial.printf("[MULTIPLEXER] Hot-swap SPI MOSI=%d MISO=%d SCLK=%d CS=%d\n", mosi, miso, sclk, cs);
    SPI.end();
    SPI.begin(sclk, miso, mosi, cs >= 0 ? cs : -1);
    return;
  }

  if (strcmp(protocolType, "PWM") == 0 || strcmp(protocolType, "pwm") == 0) {
    int pin = pins.size() > 0 ? pins[0].as<int>() : -1;
    int channel = unit["channel"] | 0;
    double freq = unit["frequency_hz"] | 5000.0;
    int resolution = unit["resolution_bits"] | 8;

    if (pin == -1) {
      logBus("PWM config skipped: missing pin");
      return;
    }

    Serial.printf("[MULTIPLEXER] Route pin %d to PWM channel %d\n", pin, channel);
    ledcSetup(channel, freq, resolution);
    ledcAttachPin(pin, channel);
    return;
  }

  if (strcmp(protocolType, "raw_gpio") == 0 || strcmp(protocolType, "gpio") == 0) {
    int pin = pins.size() > 0 ? pins[0].as<int>() : -1;
    const char *mode = unit["mode"] | "OUTPUT";
    if (pin == -1) return;

    Serial.printf("[MULTIPLEXER] GPIO pin %d mode %s\n", pin, mode);
    if (strcmp(mode, "INPUT") == 0) pinMode(pin, INPUT);
    else if (strcmp(mode, "INPUT_PULLUP") == 0) pinMode(pin, INPUT_PULLUP);
    else pinMode(pin, OUTPUT);
  }
}
