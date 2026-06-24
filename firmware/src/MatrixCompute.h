#pragma once

#include <stddef.h>
#include <stdint.h>

/** Cache-bounded INT8/2-bit matrix evaluation in IRAM — telematic vector scoring. */
class MatrixCompute {
public:
  static float evaluateTelematicVector(const float *inputVector, size_t dimensions);
  static float lastScore() { return last_score_; }

private:
  static float last_score_;
};

inline float matrixComputeScore(const float *inputVector, size_t dimensions) {
  return MatrixCompute::evaluateTelematicVector(inputVector, dimensions);
}
