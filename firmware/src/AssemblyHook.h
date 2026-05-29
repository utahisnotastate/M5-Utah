#pragma once

#include <stdint.h>

class AssemblyHook {
 public:
  static AssemblyHook &instance();

  bool applyTrampolineHook(void *targetFunc, void *newFunc);
  void removeTrampolineHook();
  bool isHooked() const;

 private:
  AssemblyHook() = default;

  uint8_t originalBytes_[4] = {0};
  void *targetedFunctionAddress_ = nullptr;
  bool isHooked_ = false;
};

AssemblyHook &loopDetour();

void nativeHookProbe();
