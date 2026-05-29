#include "DynamicMultiplexer.h"

#include "BusArbitrator.h"
#include "PriorityGatekeeper.h"

#include <SPI.h>
#include <Wire.h>

namespace {

bool g_i2cActive = false;
int g_i2cSda = -1;
int g_i2cScl = -1;

struct I2cConfigArgs {
  int sda;
  int scl;
  uint32_t frequency;
};

struct SpiConfigArgs {
  int sclk;
  int miso;
  int mosi;
  int cs;
};

struct GatekeeperBusBridge {
  BusActionFn busAction;
  void *busContext;
};

GatekeeperBusBridge g_gatekeeperBridge;

void logBus(const char *msg) {
  Serial.print("[MULTIPLEXER] ");
  Serial.println(msg);
}

void applyI2cConfig(void *context) {
  auto *args = static_cast<I2cConfigArgs *>(context);
  Wire.end();
  Wire.begin(args->sda, args->scl, args->frequency);
  g_i2cActive = true;
  g_i2cSda = args->sda;
  g_i2cScl = args->scl;
}

void applySpiConfig(void *context) {
  auto *args = static_cast<SpiConfigArgs *>(context);
  SPI.end();
  SPI.begin(args->sclk, args->miso, args->mosi, args->cs >= 0 ? args->cs : -1);
}

void gatekeeperBusDispatch(void *context) {
  auto *bridge = static_cast<GatekeeperBusBridge *>(context);
  if (bridge != nullptr && bridge->busAction != nullptr) {
    bridge->busAction(bridge->busContext);
  }
}

bool runPrioritizedBusTransaction(int lockId, int busUnitId, UBaseType_t callingPriority,
                                  BusActionFn action, void *context) {
  g_gatekeeperBridge = {action, context};
  if (globalGatekeeper().executePrioritizedAccessWithContext(
          lockId, busUnitId, callingPriority, gatekeeperBusDispatch, &g_gatekeeperBridge)) {
    return true;
  }
  if (globalBusArbitrator().executeSafeBusTransaction(busUnitId, action, context)) {
    return true;
  }
  return false;
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

void DynamicMultiplexer::configureProcessorTopology(JsonObjectConst unit, int busUnitId,
                                                    UBaseType_t callingPriority) {
  const char *protocolType = unit["type"] | unit["bus_type"] | "raw_gpio";
  JsonArrayConst pins = unit["pins"].as<JsonArrayConst>();

  if (strcmp(protocolType, "I2C") == 0 || strcmp(protocolType, "i2c") == 0) {
    I2cConfigArgs args;
    args.sda = pins.size() > 0 ? pins[0].as<int>() : (unit["sda"] | -1);
    args.scl = pins.size() > 1 ? pins[1].as<int>() : (unit["scl"] | -1);
    args.frequency = unit["frequency_hz"] | unit["i2c_frequency"] | 100000;

    if (args.sda == -1 || args.scl == -1) {
      logBus("I2C config skipped: missing SDA/SCL");
      return;
    }
    if (args.sda == args.scl) {
      logBus("I2C config rejected: pin conflict");
      return;
    }

    Serial.printf("[MULTIPLEXER] Hot-swap I2C SDA=%d SCL=%d @ %u Hz\n", args.sda, args.scl,
                  args.frequency);
    if (!runPrioritizedBusTransaction(kGateLockI2cBus, busUnitId, callingPriority, applyI2cConfig,
                                      &args)) {
      logBus("I2C transaction buffered — gatekeeper or TDMA window rejected");
    }
    return;
  }

  if (strcmp(protocolType, "SPI") == 0 || strcmp(protocolType, "spi") == 0) {
    SpiConfigArgs args;
    args.mosi = pins.size() > 0 ? pins[0].as<int>() : -1;
    args.miso = pins.size() > 1 ? pins[1].as<int>() : -1;
    args.sclk = pins.size() > 2 ? pins[2].as<int>() : -1;
    args.cs = pins.size() > 3 ? pins[3].as<int>() : -1;

    if (args.mosi == -1 || args.sclk == -1) {
      logBus("SPI config skipped: need MOSI and SCLK");
      return;
    }

    Serial.printf("[MULTIPLEXER] Hot-swap SPI MOSI=%d MISO=%d SCLK=%d CS=%d\n", args.mosi,
                  args.miso, args.sclk, args.cs);
    if (!runPrioritizedBusTransaction(kGateLockSpiBus, busUnitId, callingPriority, applySpiConfig,
                                      &args)) {
      logBus("SPI transaction buffered — gatekeeper or TDMA window rejected");
    }
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
