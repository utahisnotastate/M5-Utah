#include "TelemetryEcc.h"

#include <cstring>

uint8_t TelemetryEcc::encodeNibble(uint8_t nibble) {
  const uint8_t d0 = nibble & 0x01;
  const uint8_t d1 = (nibble >> 1) & 0x01;
  const uint8_t d2 = (nibble >> 2) & 0x01;
  const uint8_t d3 = (nibble >> 3) & 0x01;

  const uint8_t p1 = d0 ^ d1 ^ d3;
  const uint8_t p2 = d0 ^ d2 ^ d3;
  const uint8_t p3 = d1 ^ d2 ^ d3;

  return static_cast<uint8_t>((d3 << 6) | (d2 << 5) | (d1 << 4) | (p3 << 3) | (d0 << 2) | (p2 << 1) | p1);
}

uint8_t TelemetryEcc::decodeNibble(uint8_t encodedWord) {
  auto bit = [&](int index) -> uint8_t { return static_cast<uint8_t>((encodedWord >> index) & 0x01); };

  const uint8_t s1 = bit(0) ^ bit(2) ^ bit(4) ^ bit(6);
  const uint8_t s2 = bit(1) ^ bit(2) ^ bit(5) ^ bit(6);
  const uint8_t s3 = bit(3) ^ bit(4) ^ bit(5) ^ bit(6);
  const uint8_t syndrome = static_cast<uint8_t>(s1 | (s2 << 1) | (s3 << 2));

  if (syndrome != 0) {
    encodedWord ^= static_cast<uint8_t>(1u << (syndrome - 1));
  }

  return static_cast<uint8_t>(
      ((encodedWord >> 2) & 0x01) | (((encodedWord >> 4) & 0x01) << 1) |
      (((encodedWord >> 5) & 0x01) << 2) | (((encodedWord >> 6) & 0x01) << 3));
}

uint8_t telemetryStatusCode(const char *status) {
  if (status == nullptr) {
    return 0;
  }
  if (strcmp(status, "operational") == 0) {
    return 0x0;
  }
  if (strcmp(status, "degraded") == 0) {
    return 0x1;
  }
  if (strcmp(status, "error") == 0) {
    return 0x2;
  }
  return 0xF;
}
