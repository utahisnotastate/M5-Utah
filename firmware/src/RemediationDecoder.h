#pragma once

#include <Arduino.h>
#include <stdint.h>

struct __attribute__((packed)) RemediationCommand {
  uint8_t unitId;
  uint8_t safetyPin;
  uint16_t throttledFrequencyHz;
};

static constexpr uint8_t kRemediationMagic0 = 0x23;
static constexpr uint8_t kRemediationMagic1 = 0x52;
static constexpr size_t kRemediationFrameLen = 2 + sizeof(RemediationCommand);

/** Apply host `#R` closed-loop remediation throttles on Core 1. */
class RemediationDecoder {
 public:
  static bool processPayload(Stream &stream);
  static void applyCommand(const RemediationCommand &cmd);
};
