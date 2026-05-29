#include "AssemblyHook.h"

#include "TimeTravelJournal.h"

#include <Arduino.h>
#include <cstring>
#include <freertos/FreeRTOS.h>

void nativeHookProbe() {
  // Baseline probe function — safe default hook target for virtual trampolines.
}

AssemblyHook &AssemblyHook::instance() {
  static AssemblyHook hook;
  return hook;
}

AssemblyHook &loopDetour() { return AssemblyHook::instance(); }

bool AssemblyHook::isHooked() const { return isHooked_; }

bool AssemblyHook::applyTrampolineHook(void *targetFunc, void *newFunc) {
  Serial.printf("[ENCLAVE-ASSEMBLY] Preparing trampoline hook at address: %p -> %p\n", targetFunc,
                newFunc);

  if (targetFunc == nullptr || newFunc == nullptr || isHooked_) {
    return false;
  }

  targetedFunctionAddress_ = targetFunc;
  memcpy(originalBytes_, targetFunc, sizeof(originalBytes_));

  const uint32_t jumpTarget = reinterpret_cast<uint32_t>(newFunc);

  portDISABLE_INTERRUPTS();

  uint8_t *patchBuffer = static_cast<uint8_t *>(targetFunc);
  patchBuffer[0] = 0x06;
  patchBuffer[1] = static_cast<uint8_t>(jumpTarget & 0xFF);
  patchBuffer[2] = static_cast<uint8_t>((jumpTarget >> 8) & 0xFF);
  patchBuffer[3] = static_cast<uint8_t>((jumpTarget >> 16) & 0xFF);

  portENABLE_INTERRUPTS();

  isHooked_ = true;
  timeTravelRecord("assembly:hook");
  Serial.println("[SUCCESS] Assembly detour committed directly to running processor pipeline.");
  return true;
}

void AssemblyHook::removeTrampolineHook() {
  if (!isHooked_ || targetedFunctionAddress_ == nullptr) {
    return;
  }

  portDISABLE_INTERRUPTS();
  memcpy(targetedFunctionAddress_, originalBytes_, sizeof(originalBytes_));
  portENABLE_INTERRUPTS();

  isHooked_ = false;
  targetedFunctionAddress_ = nullptr;
  timeTravelRecord("assembly:unhook");
  Serial.println("[RESTORATION] Cleanly restored native processor byte maps.");
}
