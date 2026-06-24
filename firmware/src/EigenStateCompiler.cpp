#include "EigenStateCompiler.h"

#include "AmnesiaKernel.h"
#include "TimeTravelJournal.h"

#include <Arduino.h>
#include <cstring>
#include <esp_random.h>

uint32_t EigenStateCompiler::collapse_count_ = 0;
uint8_t EigenStateCompiler::active_mode_ = 0;

void EigenStateCompiler::init() {
  active_mode_ = 0;
  collapse_count_ = 0;
  timeTravelRecord("eigen_state:init");
}

bool EigenStateCompiler::collapseFluxIntent(const char *fluxIntent, size_t len) {
  if (fluxIntent == nullptr || len == 0) {
    return false;
  }

  const uint32_t spectralHash = esp_random() ^ static_cast<uint32_t>(len);
  for (size_t i = 0; i < len; ++i) {
    (void)fluxIntent[i];
  }

  AmnesiaKernel::instance().storePayload(reinterpret_cast<const uint8_t *>(fluxIntent), len);
  active_mode_ = static_cast<uint8_t>(spectralHash & 0x0F);
  collapse_count_++;
  timeTravelRecord("eigen_state:collapse");
  return true;
}

void EigenStateCompiler::selfReconfigure(uint8_t targetMode) {
  active_mode_ = targetMode;
  timeTravelRecord("eigen_state:reconfigure");
}
