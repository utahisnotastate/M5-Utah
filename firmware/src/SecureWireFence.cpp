#include "SecureWireFence.h"

#include "BinwireDecoder.h"
#include "CryptoEnclave.h"
#include "TimeTravelJournal.h"
#include "TelemetryHealth.h"
#include "registry_runtime.h"

namespace {

SecureWireFence g_secureWireFence;

bool readExact(Stream &stream, uint8_t *buffer, size_t len) {
  size_t offset = 0;
  const uint32_t start = millis();
  while (offset < len) {
    if (stream.available() > 0) {
      const int ch = stream.read();
      if (ch < 0) return false;
      buffer[offset++] = static_cast<uint8_t>(ch);
      continue;
    }
    if (millis() - start > 50) return false;
    delay(1);
  }
  return true;
}

}  // namespace

SecureWireFence &globalSecureWireFence() { return g_secureWireFence; }

bool SecureWireFence::verifyInboundSequenceFence(const SecureIntentPacket &packet) {
  const uint32_t incomingSequence = ntohl(packet.monotonicSequenceId);

  if (incomingSequence <= lastObservedSequenceId_) {
    Serial.printf(
        "[SECURITY ALERT] Dropped replay/malicious packet attempt! Detected sequence: %u <= "
        "benchmark: %u\n",
        incomingSequence, lastObservedSequenceId_);
    emitSecurityAlarm("secure_wire_replay_rejected");
    return false;
  }

  lastObservedSequenceId_ = incomingSequence;
  return true;
}

bool SecureWireDecoder_processPayload(Stream &stream) {
  SecureIntentPacket cmd{};
  if (!readExact(stream, reinterpret_cast<uint8_t *>(&cmd), sizeof(SecureIntentPacket))) {
    return false;
  }

  const uint16_t dataVector = ntohs(cmd.dataVector);
  const uint32_t sequenceId = ntohl(cmd.monotonicSequenceId);

  Serial.printf(
      "[SECURE WIRE] Unit %u | Opcode %u | Vector %u | Seq %u\n", cmd.unitId, cmd.opcode,
      dataVector, sequenceId);

  timeTravelRecord("secure_wire:attested");
  telemetryHealthRecordFastPath(cmd.unitId, cmd.opcode);

  char unitName[16];
  snprintf(unitName, sizeof(unitName), "u%u", cmd.unitId);
  registryApplyBinwireUnit(unitName, cmd.opcode, dataVector, sequenceId);

  if (cmd.opcode > 0 && cmd.opcode <= 48) {
    pinMode(cmd.opcode, OUTPUT);
    digitalWrite(cmd.opcode, HIGH);
  }
  return true;
}
