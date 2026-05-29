#include "ResourceOrchestrator.h"

#include "BusArbitrator.h"
#include "HandleMemory.h"
#include "TimeTravelJournal.h"

#include <Arduino.h>
#include <cstring>

namespace {

constexpr uint32_t kElevatedHeapThreshold = 28000;
constexpr uint32_t kCriticalHeapThreshold = 22000;
constexpr uint32_t kHandlePoolPressureRatio = 85;

}  // namespace

ResourceOrchestrator &globalResourceOrchestrator() {
  static ResourceOrchestrator orchestrator;
  return orchestrator;
}

void ResourceOrchestrator::initialize() {
  lastPressure_ = ResourcePressureLevel::Nominal;
  deferredFrames_ = 0;
  stagedContexts_ = 0;
  pressureTicks_ = 0;
  Serial.println("[ORCHESTRATOR] Resource-aware execution staging online.");
}

ResourcePressureLevel ResourceOrchestrator::evaluatePressure(uint32_t freeHeapBytes) const {
  const size_t poolTop = globalMemoryManager().poolTop();
  const size_t poolLimit = globalMemoryManager().poolLimit();
  const bool handlePressure =
      poolLimit > 0 && ((poolTop * 100) / poolLimit) >= kHandlePoolPressureRatio;
  const bool busPressure = globalBusArbitrator().rejectedTransactions() > 8;

  if (freeHeapBytes < kCriticalHeapThreshold || handlePressure) {
    return ResourcePressureLevel::Critical;
  }
  if (freeHeapBytes < kElevatedHeapThreshold || busPressure) {
    return ResourcePressureLevel::Elevated;
  }
  return ResourcePressureLevel::Nominal;
}

void ResourceOrchestrator::orchestrateTick(uint32_t freeHeapBytes) {
  lastPressure_ = evaluatePressure(freeHeapBytes);
  if (lastPressure_ != ResourcePressureLevel::Nominal) {
    pressureTicks_++;
  }

  if (lastPressure_ == ResourcePressureLevel::Critical) {
    globalMemoryManager().compactIfPressure(0.85f);
  }
}

bool ResourceOrchestrator::shouldDeferNonCriticalIntents() const {
  return lastPressure_ == ResourcePressureLevel::Critical;
}

bool ResourceOrchestrator::shouldStageSpeculatively() const {
  return lastPressure_ == ResourcePressureLevel::Nominal;
}

bool ResourceOrchestrator::allowIntentDispatch(bool isRegistryMutation,
                                               bool isBinaryFastPath) const {
  if (lastPressure_ != ResourcePressureLevel::Critical) {
    return true;
  }
  return isRegistryMutation || isBinaryFastPath;
}

void ResourceOrchestrator::recordDeferredFrame() { deferredFrames_++; }

uint32_t ResourceOrchestrator::deferredFrameCount() const { return deferredFrames_; }

uint32_t ResourceOrchestrator::stagedContextCount() const { return stagedContexts_; }

ResourcePressureLevel ResourceOrchestrator::lastPressureLevel() const { return lastPressure_; }

bool jsonPayloadIsNonCritical(const char *payload, size_t length) {
  if (payload == nullptr || length == 0) {
    return true;
  }
  if (payload[0] != '{') {
    return true;
  }

  static const char *kCriticalKeys[] = {"\"registry\"", "\"native_jit\"", "\"memory_compact\""};
  for (const char *key : kCriticalKeys) {
    const size_t keyLen = strlen(key);
    for (size_t i = 0; i + keyLen <= length; i++) {
      if (memcmp(payload + i, key, keyLen) == 0) {
        return false;
      }
    }
  }
  return true;
}
