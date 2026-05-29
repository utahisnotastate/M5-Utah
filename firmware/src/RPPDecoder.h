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

struct __attribute__((packed)) RPPCommandPacket {
  uint8_t unitId;
  uint8_t opcode;
  uint16_t dataVector;
  uint32_t sequenceId;
};

static constexpr size_t kRppFrameLen = 2 + sizeof(RPPCommandPacket);
static constexpr uint8_t kRppMagic0 = 0x23;
static constexpr uint8_t kRppMagic1 = 0x50;

static constexpr uint8_t kRppOpcodePinHigh = 0x01;
static constexpr uint8_t kRppOpcodePinLow = 0x02;
static constexpr uint8_t kRppOpcodeSetFrequency = 0x03;

/** Direct-Execution Kernel (DEK) — stack-local RPP dispatch without JSON heap. */
class MicroExecutionKernel {
 public:
  static bool tryProcess(Stream &stream);
  static bool processPayload(Stream &stream);
  static void applyCommand(const RPPCommandPacket &cmd);
};

void applyRppMutation(uint8_t unitId, uint8_t opcode, uint16_t dataVector, uint32_t sequenceId);
