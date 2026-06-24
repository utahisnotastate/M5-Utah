#pragma once

#include <csetjmp>

#include <stdint.h>

/** Pre-emptive execution entropy monitor — avoids fatal paths via setjmp shield. */
class CausalDebugger {
public:
  static void init();
  static uint32_t avoidedCrashCount() { return avoided_count_; }
  static uint32_t lastPipelineStress() { return last_stress_; }

  template <typename Func>
  static void executeWithProbabilityShield(Func unsafeBlock) {
    const uint32_t baseline = measureCpuPipelineStress();
    if (setjmp(causal_anchor_) == 0) {
      unsafeBlock();
    } else {
      applyThermodynamicPatch(baseline, measureCpuPipelineStress());
      logAvoidedProbability();
      avoided_count_++;
    }
    last_stress_ = measureCpuPipelineStress();
  }

private:
  static uint32_t measureCpuPipelineStress();
  static void applyThermodynamicPatch(uint32_t base, uint32_t spike);
  static void logAvoidedProbability();

  static jmp_buf causal_anchor_;
  static uint32_t avoided_count_;
  static uint32_t last_stress_;
};

inline void causalDebuggerInit() { CausalDebugger::init(); }
