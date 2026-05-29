#include "RPPDecoder.h"

#include "PriorityGatekeeper.h"
#include "TelemetryHealth.h"
#include "TimeTravelJournal.h"
#include "registry_runtime.h"

#include <cstring>

namespace {

constexpr int kMaxPin = 48;

struct RppExecContext {
  RPPCommandPacket cmd;
};

void executeRppHardware(const RPPCommandPacket &cmd) {
  const uint16_t parameterValue = ntohs(cmd.dataVector);
  const uint32_t sequenceId = ntohl(cmd.sequenceId);

  applyRppMutation(cmd.unitId, cmd.opcode, parameterValue, sequenceId);
  telemetryHealthRecordFastPath(cmd.unitId, static_cast<uint8_t>(parameterValue & 0xFF));

  if (cmd.opcode == kRppOpcodePinHigh && parameterValue > 0 && parameterValue <= kMaxPin) {
    pinMode(parameterValue, OUTPUT);
    digitalWrite(parameterValue, HIGH);
    return;
  }

  if (cmd.opcode == kRppOpcodePinLow && parameterValue > 0 && parameterValue <= kMaxPin) {
    pinMode(parameterValue, OUTPUT);
    digitalWrite(parameterValue, LOW);
  }

  (void)sequenceId;
}

void rppGatekeeperTrampoline(void *raw) {
  auto *ctx = static_cast<RppExecContext *>(raw);
  if (ctx != nullptr) {
    executeRppHardware(ctx->cmd);
  }
}

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

void applyRppMutation(uint8_t unitId, uint8_t opcode, uint16_t dataVector, uint32_t sequenceId) {
  char unitName[16];
  snprintf(unitName, sizeof(unitName), "u%u", unitId);
  registryApplyBinwireUnit(unitName, static_cast<uint8_t>(dataVector & 0xFF), dataVector, sequenceId);
  (void)opcode;
}

void MicroExecutionKernel::applyCommand(const RPPCommandPacket &cmd) {
  const uint16_t parameterValue = ntohs(cmd.dataVector);

  Serial.printf("[RPP NATIVE INTERCEPT] Executed Opcode %u on Unit %u with Parameter %u\n",
                cmd.opcode, cmd.unitId, parameterValue);

  timeTravelRecord("rpp:micro_exec");

  RppExecContext ctx{};
  ctx.cmd = cmd;
  const UBaseType_t callingPriority = uxTaskPriorityGet(xTaskGetCurrentTaskHandle());
  if (!globalGatekeeper().executePrioritizedAccessWithContext(
          kGateLockI2cBus, cmd.unitId, callingPriority, rppGatekeeperTrampoline, &ctx)) {
    executeRppHardware(cmd);
  }
}

bool MicroExecutionKernel::processPayload(Stream &stream) {
  RPPCommandPacket cmd;
  if (!readExact(stream, reinterpret_cast<uint8_t *>(&cmd), sizeof(RPPCommandPacket))) {
    return false;
  }
  applyCommand(cmd);
  return true;
}

bool MicroExecutionKernel::tryProcess(Stream &stream) {
  if (stream.available() < static_cast<int>(kRppFrameLen)) {
    return false;
  }
  if (stream.peek() != kRppMagic0) {
    return false;
  }

  uint8_t header[2];
  if (!readExact(stream, header, 2)) {
    return false;
  }
  if (header[0] != kRppMagic0 || header[1] != kRppMagic1) {
    return false;
  }

  return processPayload(stream);
}
