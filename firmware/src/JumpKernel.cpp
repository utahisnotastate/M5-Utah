#include "JumpKernel.h"

#include "PriorityGatekeeper.h"
#include "TimeTravelJournal.h"

namespace {

FlattenedExecutionRoutine g_jumpTableMatrix[kMaxJumpTableSlots] = {};
BranchStateMirrorEntry g_branchMirror[kMaxJumpTableSlots] = {};

void noopJumpRoutine() {}

struct JumpExecContext {
  uint8_t functionSlot;
};

void jumpGatekeeperTrampoline(void *raw) {
  auto *ctx = static_cast<JumpExecContext *>(raw);
  if (ctx == nullptr) {
    return;
  }
  const uint8_t slot = ctx->functionSlot;
  if (slot < kMaxJumpTableSlots && g_jumpTableMatrix[slot] != nullptr) {
    g_jumpTableMatrix[slot]();
  }
}

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

void dispatchJumpRoutine(uint8_t functionSlot, uint16_t priorityMask) {
  if (functionSlot >= kMaxJumpTableSlots || g_jumpTableMatrix[functionSlot] == nullptr) {
    return;
  }

  JumpExecContext ctx{};
  ctx.functionSlot = functionSlot;
  const UBaseType_t callingPriority = uxTaskPriorityGet(xTaskGetCurrentTaskHandle());
  const uint8_t gateTier = static_cast<uint8_t>((priorityMask >> 8) & 0xFF);
  if (!globalGatekeeper().executePrioritizedAccessWithContext(
          kGateLockI2cBus, gateTier, callingPriority, jumpGatekeeperTrampoline, &ctx)) {
    g_jumpTableMatrix[functionSlot]();
  }
}

}  // namespace

void jumpKernelInitDefaults() { MicroJumpKernel::initDefaults(); }

void MicroJumpKernel::initDefaults() {
  for (int i = 0; i < kMaxJumpTableSlots; ++i) {
    g_jumpTableMatrix[i] = nullptr;
    g_branchMirror[i].functionSlot = 0;
    g_branchMirror[i].priorityMask = 0;
    g_branchMirror[i].valid = 0;
  }
  g_jumpTableMatrix[0] = noopJumpRoutine;
}

void MicroJumpKernel::registerRoutine(uint8_t slot, FlattenedExecutionRoutine routine) {
  if (slot < kMaxJumpTableSlots) {
    g_jumpTableMatrix[slot] = routine;
  }
}

FlattenedExecutionRoutine MicroJumpKernel::getRoutine(uint8_t slot) {
  if (slot >= kMaxJumpTableSlots) {
    return nullptr;
  }
  return g_jumpTableMatrix[slot];
}

const BranchStateMirrorEntry *MicroJumpKernel::mirrorEntry(uint8_t conditionId) {
  if (conditionId >= kMaxJumpTableSlots) {
    return nullptr;
  }
  return &g_branchMirror[conditionId];
}

void MicroJumpKernel::applyJumpVector(const JumpVectorCommand &cmd) {
  const uint16_t priorityMask = ntohs(cmd.priorityMask);
  const uint8_t condition = cmd.conditionId;
  const uint8_t slot = cmd.functionSlot;

  Serial.printf(
      "[BRANCH FASTPATH] Mapping condition slot %u directly to function pointer slot %u\n",
      condition, slot);

  timeTravelRecord("branch:flatten");

  if (condition < kMaxJumpTableSlots) {
    g_branchMirror[condition].functionSlot = slot;
    g_branchMirror[condition].priorityMask = priorityMask;
    g_branchMirror[condition].valid = 1;
  }

  dispatchJumpRoutine(slot, priorityMask);
}

bool MicroJumpKernel::processPayload(Stream &stream) {
  JumpVectorCommand cmd{};
  if (!readExact(stream, reinterpret_cast<uint8_t *>(&cmd), sizeof(JumpVectorCommand))) {
    return false;
  }
  applyJumpVector(cmd);
  return true;
}
