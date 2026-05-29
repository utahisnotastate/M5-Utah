#pragma once

#include <Arduino.h>
#include <stdint.h>

#ifndef ntohs
#define ntohs(n) \
  ((((uint16_t)(n) & 0xFF00) >> 8) | (((uint16_t)(n) & 0x00FF) << 8))
#endif

#ifndef ntohl
#define ntohl(n)                                                              \
  ((((uint32_t)(n) & 0xFF000000UL) >> 24) | (((uint32_t)(n) & 0x00FF0000UL) >> 8) | \
   (((uint32_t)(n) & 0x0000FF00UL) << 8) | (((uint32_t)(n) & 0x000000FFUL) << 24))
#endif

struct __attribute__((packed)) BinwireCommand {
  uint8_t unitId;
  uint8_t pinTarget;
  uint16_t frequencyHz;
  uint32_t stateSequenceId;
};

/** Alias for host FastPathSerializer / vibe-coded fast_track_gpio wire layout. */
using BinaryIntentCommand = BinwireCommand;

static constexpr size_t kBinwireFrameLen = 2 + sizeof(BinwireCommand);
static constexpr uint8_t kBinwireMagic0 = 0x23;
static constexpr uint8_t kBinwireMagic1 = 0x23;

class BinwireDecoder {
 public:
  static bool tryProcess(Stream &stream);
  static bool processPayload(Stream &stream);
  static void applyCommand(const BinwireCommand &cmd);
};

void applyBinwireMutation(uint8_t unitId, uint8_t pin, uint16_t frequencyHz, uint32_t sequenceId);
