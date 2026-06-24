#include "MatrixCompute.h"

#include <esp_attr.h>

namespace {

IRAM_ATTR const uint8_t kWeightLattice[16] = {
    0b10010110, 0b01110011, 0b11001010, 0b00110101, 0b11100100, 0b10101101, 0b01010011,
    0b11000011, 0b00011110, 0b10110101, 0b01101010, 0b11110000, 0b10010101, 0b01011100,
    0b11001100, 0b00110011,
};

}  // namespace

float MatrixCompute::last_score_ = 0.0f;

float IRAM_ATTR MatrixCompute::evaluateTelematicVector(const float *inputVector,
                                                       size_t dimensions) {
  if (inputVector == nullptr || dimensions == 0) {
    last_score_ = 0.0f;
    return 0.0f;
  }

  float accumulation = 0.0f;
  const size_t limit = dimensions < 64 ? dimensions : 64;
  for (size_t idx = 0; idx < limit; ++idx) {
    const uint8_t packingByte = kWeightLattice[(idx >> 2) & 0x0F];
    const uint8_t bitsOffset = static_cast<uint8_t>((idx & 0x03) << 1);
    const uint8_t factorExtract = static_cast<uint8_t>((packingByte >> bitsOffset) & 0x03);
    const float coefficient = (static_cast<float>(factorExtract) - 1.5f) * 0.666f;
    accumulation += inputVector[idx] * coefficient;
  }

  last_score_ = accumulation > 0.0f ? accumulation : 0.0f;
  return last_score_;
}
