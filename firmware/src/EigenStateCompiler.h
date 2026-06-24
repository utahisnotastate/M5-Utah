#pragma once

#include <stddef.h>
#include <stdint.h>

/** Eigen-state intent collapse — spectral hardware alignment without IDE compile step. */
class EigenStateCompiler {
public:
  static void init();
  static bool collapseFluxIntent(const char *fluxIntent, size_t len);
  static void selfReconfigure(uint8_t targetMode);
  static uint32_t collapseCount() { return collapse_count_; }
  static uint8_t activeMode() { return active_mode_; }

private:
  static uint32_t collapse_count_;
  static uint8_t active_mode_;
};

inline void eigenStateCompilerInit() { EigenStateCompiler::init(); }
