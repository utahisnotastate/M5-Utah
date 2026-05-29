#pragma once

#include <stdint.h>

class TelemetryEcc {
 public:
  static uint8_t encodeNibble(uint8_t nibble);
  static uint8_t decodeNibble(uint8_t encodedWord);
};

uint8_t telemetryStatusCode(const char *status);
