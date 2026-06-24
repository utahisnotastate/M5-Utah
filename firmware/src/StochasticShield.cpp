#include "StochasticShield.h"

#include "TimeTravelJournal.h"

#include <Arduino.h>
#include <esp_random.h>

namespace {

bool g_initialized = false;
uint32_t g_thermodynamic_seed = 0;

#if defined(ARDUINO_ARCH_ESP32)
uint32_t sampleAdcThermalNoise() {
  uint32_t mix = 0;
  for (int i = 0; i < 6; ++i) {
    // Uncalibrated ADC picks up ambient thermal / RF noise on floating inputs.
    mix ^= static_cast<uint32_t>(analogReadMilliVolts(1)) << ((i % 4) * 8);
    mix ^= static_cast<uint32_t>(micros());
    delayMicroseconds(2);
  }
  return mix;
}
#endif

}  // namespace

void StochasticShield::init() {
  if (g_initialized) {
    return;
  }
  g_thermodynamic_seed = harvestThermodynamicEntropy();
  g_initialized = true;
  timeTravelRecord("stochastic_shield:init");
}

uint32_t StochasticShield::harvestThermodynamicEntropy() {
  uint32_t entropy = esp_random();
#if defined(ARDUINO_ARCH_ESP32)
  entropy ^= sampleAdcThermalNoise();
#if defined(CONFIG_IDF_TARGET_ESP32) || defined(CONFIG_IDF_TARGET_ESP32S3)
  entropy ^= static_cast<uint32_t>(temperatureRead() * 1000.0f);
#endif
#endif
  return entropy;
}

uint32_t StochasticShield::brownianEntropy() {
  return esp_random() ^ g_thermodynamic_seed ^ harvestThermodynamicEntropy();
}

uint32_t StochasticShield::jitterMicros() {
  return (brownianEntropy() & 0x0F) + 1;
}

void StochasticShield::executeWithBrownianJitter(void (*criticalTask)(void)) {
  if (criticalTask == nullptr) {
    return;
  }
  delayMicroseconds(jitterMicros());
  criticalTask();
  delayMicroseconds((brownianEntropy() & 0x1F) + 1);
}

void StochasticShield::executeWithBrownianJitter(void (*criticalTask)(void *), void *context) {
  if (criticalTask == nullptr) {
    return;
  }
  delayMicroseconds(jitterMicros());
  criticalTask(context);
  delayMicroseconds((brownianEntropy() & 0x1F) + 1);
}
