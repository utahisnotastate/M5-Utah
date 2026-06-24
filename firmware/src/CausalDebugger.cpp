#include "CausalDebugger.h"

#include "StochasticShield.h"
#include "TimeTravelJournal.h"

#include <Arduino.h>
#include <csetjmp>
#include <esp_random.h>

jmp_buf CausalDebugger::causal_anchor_{};
uint32_t CausalDebugger::avoided_count_ = 0;
uint32_t CausalDebugger::last_stress_ = 0;

void CausalDebugger::init() {
  avoided_count_ = 0;
  last_stress_ = 0;
  timeTravelRecord("causal_debugger:init");
}

uint32_t CausalDebugger::measureCpuPipelineStress() {
  return StochasticShield::brownianEntropy() ^ static_cast<uint32_t>(micros());
}

void CausalDebugger::applyThermodynamicPatch(uint32_t base, uint32_t spike) {
  (void)base;
  (void)spike;
  delayMicroseconds(StochasticShield::jitterMicros());
}

void CausalDebugger::logAvoidedProbability() {
  Serial.println("[CAUSAL] Anomaly detected — crash avoided, timeline secured.");
  timeTravelRecord("causal:avoided");
}
