#pragma once

#include <Arduino.h>
#include <stdint.h>

struct __attribute__((packed)) StreamingIntentCommand {
  uint8_t unitId;
  uint8_t modeFlag;
  uint16_t frequencyHz;
};

static constexpr uint8_t kStreamMagic0 = 0x23;
static constexpr uint8_t kStreamMagic1 = 0x53;
static constexpr size_t kStreamFrameLen = 2 + sizeof(StreamingIntentCommand);

/** Core 1 zero-copy stream intent dispatch for `#S` frames from CrossCorePipe. */
class StreamIntentDecoder {
 public:
  static bool processPayload(Stream &stream);
  static void applyCommand(const StreamingIntentCommand &cmd);
};
