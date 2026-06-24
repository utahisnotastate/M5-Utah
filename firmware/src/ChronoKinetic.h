#pragma once

#include <stdint.h>

/** Intent-state attraction servo relaxation — golden-ratio PWM collapse (no PID). */
class ChronoKinetic {
public:
  static void init();
  static void relaxToCoordinate(int servoChannel, float currentAngle, float targetIntent);
  static float lastTarget() { return last_target_; }
  static int lastPwm() { return last_pwm_; }

private:
  static int calculateLatentAttraction(float entropyDelta);
  static float last_target_;
  static int last_pwm_;
};

inline void chronoKineticInit() { ChronoKinetic::init(); }
