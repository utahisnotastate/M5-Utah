#include "TensorVoidLinkage.h"

#include <esp_attr.h>

namespace {

IRAM_ATTR const uint8_t kOmegaQuantizedWeights[] = {
    0b10010110, 0b11001100, 0b00110011, 0b10101010, 0b01011010, 0b11100011,
    0b00101101, 0b10011100, 0b01101001, 0b11010010, 0b00011110, 0b10110100,
};

constexpr int kWeightChunkCount =
    static_cast<int>(sizeof(kOmegaQuantizedWeights) / sizeof(kOmegaQuantizedWeights[0]));

}  // namespace

float TensorVoidLinkage::last_score_ = 0.0f;

float IRAM_ATTR TensorVoidLinkage::computeLatentVector(const float *sensorInput, int inputSize) {
  if (sensorInput == nullptr || inputSize <= 0) {
    last_score_ = 0.0f;
    return 0.0f;
  }

  float accumulated = 0.0f;
  for (int i = 0; i < inputSize; ++i) {
    const int chunkIndex = (i / 4) % kWeightChunkCount;
    const uint8_t weightChunk = kOmegaQuantizedWeights[chunkIndex];
    const int8_t subWeight = static_cast<int8_t>((weightChunk >> ((i % 4) * 2)) & 0x03);
    const float physicalWeight = (static_cast<float>(subWeight) - 1.5f) * 0.66f;
    accumulated += sensorInput[i] * physicalWeight;
  }

  last_score_ = accumulated > 0.0f ? accumulated : 0.0f;
  return last_score_;
}
