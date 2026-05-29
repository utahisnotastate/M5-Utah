#pragma once

#include <Arduino.h>
#include <stdint.h>

#ifndef ntohs
#define ntohs(n) \
  ((((uint16_t)(n) & 0xFF00) >> 8) | (((uint16_t)(n) & 0x00FF) << 8))
#endif

struct __attribute__((packed)) JumpVectorCommand {
  uint8_t conditionId;
  uint8_t functionSlot;
  uint16_t priorityMask;
};

using FlattenedExecutionRoutine = void (*)();

struct BranchStateMirrorEntry {
  volatile uint8_t functionSlot;
  volatile uint16_t priorityMask;
  volatile uint8_t valid;
};

static constexpr size_t kJumpFlattenFrameLen = 2 + sizeof(JumpVectorCommand);
static constexpr uint8_t kJumpFlattenMagic0 = 0x23;
static constexpr uint8_t kJumpFlattenMagic1 = 0x46;
static constexpr int kMaxJumpTableSlots = 16;

/** Micro-Jump Kernel — lockless branch mirror + function-pointer jump table. */
class MicroJumpKernel {
 public:
  static bool processPayload(Stream &stream);
  static void applyJumpVector(const JumpVectorCommand &cmd);
  static void registerRoutine(uint8_t slot, FlattenedExecutionRoutine routine);
  static FlattenedExecutionRoutine getRoutine(uint8_t slot);
  static const BranchStateMirrorEntry *mirrorEntry(uint8_t conditionId);
  static void initDefaults();
};

void jumpKernelInitDefaults();
