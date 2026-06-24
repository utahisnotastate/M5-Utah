#include "BiosymmetricBus.h"

#include "TimeTravelJournal.h"

#include <Arduino.h>

namespace {

#if defined(CONFIG_IDF_TARGET_ESP32)
constexpr int kDacPin = 25;
constexpr int kAdcPin = 36;
constexpr bool kHasDac = true;
#else
constexpr int kAdcPin = 1;
constexpr bool kHasDac = false;
#endif

}  // namespace

bool BiosymmetricBus::active_ = false;
uint32_t BiosymmetricBus::activation_count_ = 0;

void BiosymmetricBus::initOrganicSubstrate() {
#if kHasDac
  pinMode(kAdcPin, INPUT);
  active_ = true;
  timeTravelRecord("biosymmetric:init");
#else
  active_ = false;
#endif
}

int BiosymmetricBus::mapTensorToVoltage(float tensor) {
  if (tensor < -1.0f) {
    tensor = -1.0f;
  }
  if (tensor > 1.0f) {
    tensor = 1.0f;
  }
  return static_cast<int>((tensor + 1.0f) * 127.5f);
}

float BiosymmetricBus::mapVoltageToTensor(int voltage) {
  return (static_cast<float>(voltage) / 2047.5f) - 1.0f;
}

float BiosymmetricBus::applyOrganicActivation(float latentTensorValue) {
  if (!active_) {
    return latentTensorValue > 0.0f ? latentTensorValue : 0.0f;
  }

#if kHasDac
  const int stimulus = mapTensorToVoltage(latentTensorValue);
  dacWrite(kDacPin, stimulus);
  delayMicroseconds(1);
  const int response = analogRead(kAdcPin);
  activation_count_++;
  return mapVoltageToTensor(response);
#else
  const int response = analogReadMilliVolts(kAdcPin);
  activation_count_++;
  return mapVoltageToTensor(response);
#endif
}
