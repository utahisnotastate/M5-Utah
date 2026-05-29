#pragma once

#include <stddef.h>
#include <stdint.h>

enum class ResourcePressureLevel : uint8_t {
  Nominal = 0,
  Elevated = 1,
  Critical = 2,
};

class ResourceOrchestrator {
 public:
  void initialize();
  ResourcePressureLevel evaluatePressure(uint32_t freeHeapBytes) const;
  void orchestrateTick(uint32_t freeHeapBytes);
  bool shouldDeferNonCriticalIntents() const;
  bool shouldStageSpeculatively() const;
  bool allowIntentDispatch(bool isRegistryMutation, bool isBinaryFastPath) const;
  void recordDeferredFrame();
  uint32_t deferredFrameCount() const;
  uint32_t stagedContextCount() const;
  ResourcePressureLevel lastPressureLevel() const;

 private:
  ResourcePressureLevel lastPressure_ = ResourcePressureLevel::Nominal;
  uint32_t deferredFrames_ = 0;
  uint32_t stagedContexts_ = 0;
  uint32_t pressureTicks_ = 0;
};

ResourceOrchestrator &globalResourceOrchestrator();

bool jsonPayloadIsNonCritical(const char *payload, size_t length);
