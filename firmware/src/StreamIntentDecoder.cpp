#include "StreamIntentDecoder.h"

#include "TelemetryHealth.h"
#include "TimeTravelJournal.h"
#include "registry_runtime.h"

namespace {

bool readExact(Stream &stream, uint8_t *buffer, size_t len) {
  size_t offset = 0;
  const uint32_t start = millis();
  while (offset < len) {
    if (stream.available() > 0) {
      const int ch = stream.read();
      if (ch < 0) {
        return false;
      }
      buffer[offset++] = static_cast<uint8_t>(ch);
      continue;
    }
    if (millis() - start > 50) {
      return false;
    }
    delay(1);
  }
  return true;
}

uint16_t ntohs16(uint16_t value) {
  return static_cast<uint16_t>(((value & 0xFF00) >> 8) | ((value & 0x00FF) << 8));
}

}  // namespace

void StreamIntentDecoder::applyCommand(const StreamingIntentCommand &cmd) {
  const uint16_t frequency = ntohs16(cmd.frequencyHz);
  Serial.printf(
      "[CORE 1 PIPE] Executed zero-copy patch: unit %u mode %u -> freq %u Hz\n", cmd.unitId,
      cmd.modeFlag, frequency);
  timeTravelRecord("stream:zero_copy");
  telemetryHealthRecordFastPath(cmd.unitId, cmd.modeFlag);
  char unitName[16];
  snprintf(unitName, sizeof(unitName), "u%u", cmd.unitId);
  registryApplyBinwireUnit(unitName, cmd.modeFlag, frequency, 0);
}

bool StreamIntentDecoder::processPayload(Stream &stream) {
  StreamingIntentCommand cmd{};
  if (!readExact(stream, reinterpret_cast<uint8_t *>(&cmd), sizeof(cmd))) {
    return false;
  }
  applyCommand(cmd);
  return true;
}
