#include "ChronoKinetic.h"

#include "MatrixCompute.h"
#include "TimeTravelJournal.h"

#include <Arduino.h>

namespace {

constexpr int kPwmChannel = 3;
constexpr int kPwmPin = 26;
constexpr int kPwmResolution = 12;
constexpr int kPwmFrequency = 50;
constexpr float kGoldenRatio = 0.618f;

}  // namespace

float ChronoKinetic::last_target_ = 0.0f;
int ChronoKinetic::last_pwm_ = 0;

void ChronoKinetic::init() {
  ledcSetup(kPwmChannel, kPwmFrequency, kPwmResolution);
  ledcAttachPin(kPwmPin, kPwmChannel);
  timeTravelRecord("chrono_kinetic:init");
}

int ChronoKinetic::calculateLatentAttraction(float entropy) {
  const int pwm = static_cast<int>(4096.0f + (entropy * kGoldenRatio * 256.0f));
  if (pwm < 0) {
    return 0;
  }
  if (pwm > 4095) {
    return 4095;
  }
  return pwm;
}

void ChronoKinetic::relaxToCoordinate(int servoChannel, float currentAngle, float targetIntent) {
  (void)servoChannel;
  const float entropyDelta = targetIntent - currentAngle;
  const float latent = MatrixCompute::lastScore();
  const float blendedTarget = targetIntent + latent * 0.01f;
  const float blendedDelta = blendedTarget - currentAngle;
  last_target_ = blendedTarget;
  last_pwm_ = calculateLatentAttraction(blendedDelta);
  ledcWrite(kPwmChannel, last_pwm_);
}
