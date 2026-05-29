#include "BinwireDecoder.h"

#include "TimeTravelJournal.h"
#include "TelemetryHealth.h"
#include "registry_runtime.h"

#include <cstring>

namespace {

constexpr int kMaxPin = 48;

bool readExact(Stream &stream, uint8_t *buffer, size_t len) {
  size_t offset = 0;
  uint32_t start = millis();
  while (offset < len) {
    if (stream.available() > 0) {
      int ch = stream.read();
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

void applyBinwireMutation(uint8_t unitId, uint8_t pin, uint16_t frequencyHz, uint32_t sequenceId) {
  char unitName[16];
  snprintf(unitName, sizeof(unitName), "u%u", unitId);
  registryApplyBinwireUnit(unitName, pin, frequencyHz, sequenceId);
}

void BinwireDecoder::applyCommand(const BinwireCommand &cmd) {
  const uint16_t freq = ntohs(cmd.frequencyHz);
  const uint32_t seq = ntohl(cmd.stateSequenceId);

  Serial.printf("[BINWIRE FASTPATH] Unit %u | Pin %u | Freq %u Hz | Seq %u\n", cmd.unitId,
                cmd.pinTarget, freq, seq);

  timeTravelRecord("binwire:fastpath");

  telemetryHealthRecordFastPath(cmd.unitId, cmd.pinTarget);

  applyBinwireMutation(cmd.unitId, cmd.pinTarget, freq, seq);

  if (cmd.pinTarget > 0 && cmd.pinTarget <= kMaxPin) {
    pinMode(cmd.pinTarget, OUTPUT);
    digitalWrite(cmd.pinTarget, HIGH);
  }
}

bool BinwireDecoder::processPayload(Stream &stream) {
  BinwireCommand cmd;
  if (!readExact(stream, reinterpret_cast<uint8_t *>(&cmd), sizeof(BinwireCommand))) {
    return false;
  }
  applyCommand(cmd);
  return true;
}

bool BinwireDecoder::tryProcess(Stream &stream) {
  if (stream.available() < static_cast<int>(kBinwireFrameLen)) {
    return false;
  }
  if (stream.peek() != kBinwireMagic0) {
    return false;
  }

  uint8_t header[2];
  if (!readExact(stream, header, 2)) {
    return false;
  }
  if (header[0] != kBinwireMagic0 || header[1] != kBinwireMagic1) {
    return false;
  }

  return processPayload(stream);
}
