#pragma once

#include <Arduino.h>
#include <stdint.h>

struct __attribute__((packed)) SecureIntentPacket {
  uint8_t unitId;
  uint8_t opcode;
  uint16_t dataVector;
  uint32_t monotonicSequenceId;
};

static constexpr uint8_t kSecureWireMagic0 = 0x23;
static constexpr uint8_t kSecureWireMagic1 = 0x41;
static constexpr size_t kSecureWireFrameLen = 2 + sizeof(SecureIntentPacket);

/** Monotonic anti-replay fence validated on Core 0 ingest (m5-secure). */
class SecureWireFence {
 public:
  bool verifyInboundSequenceFence(const SecureIntentPacket &packet);
  uint32_t lastObservedSequenceId() const { return lastObservedSequenceId_; }

 private:
  uint32_t lastObservedSequenceId_ = 0;
};

SecureWireFence &globalSecureWireFence();

bool SecureWireDecoder_processPayload(Stream &stream);
