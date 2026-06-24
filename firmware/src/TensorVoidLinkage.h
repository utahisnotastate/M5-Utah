#pragma once

#include <stdint.h>

/** 2-bit quantized latent scoring in IRAM — sub-register inference path. */
class TensorVoidLinkage {
public:
  static float computeLatentVector(const float *sensorInput, int inputSize);
  static float lastScore() { return last_score_; }

private:
  static float last_score_;
};

inline float tensorVoidScore(const float *sensorInput, int inputSize) {
  return TensorVoidLinkage::computeLatentVector(sensorInput, inputSize);
}
