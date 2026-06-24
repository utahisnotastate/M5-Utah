#include "SpatialUI.h"

#include "StochasticShield.h"
#include "TimeTravelJournal.h"

#include <M5Unified.h>
#include <Arduino.h>

namespace {

constexpr int kMagneticPin = 2;
constexpr int kGammaHz = 40;
constexpr int kPwmChannel = 4;
constexpr int kPwmResolution = 8;

}  // namespace

bool SpatialUI::active_ = false;
uint32_t SpatialUI::frames_projected_ = 0;

void SpatialUI::initRetinalProjection() {
  M5.Display.setBrightness(0);
  ledcSetup(kPwmChannel, kGammaHz * 1000, kPwmResolution);
  ledcAttachPin(kMagneticPin, kPwmChannel);
  active_ = true;
  timeTravelRecord("spatial_ui:init");
}

int SpatialUI::mapLuminosityToFlux(uint8_t pixel) {
  return static_cast<int>((static_cast<float>(pixel) / 255.0f) * 255.0f);
}

void SpatialUI::projectHolographicFrame(const uint8_t *videoBuffer, size_t bufferSize) {
  if (!active_ || videoBuffer == nullptr || bufferSize == 0) {
    return;
  }

  const size_t stride = bufferSize > 64 ? 64 : bufferSize;
  for (size_t i = 0; i < bufferSize; i += stride) {
    const uint8_t luminosity = videoBuffer[i];
    ledcWrite(kPwmChannel, mapLuminosityToFlux(luminosity));
    delayMicroseconds(25);
  }
  frames_projected_++;
}
