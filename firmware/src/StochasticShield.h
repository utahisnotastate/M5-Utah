#pragma once

#include <stdint.h>

/** Thermodynamic clock jitter — masks deterministic execution timing (Brownian shield). */
class StochasticShield {
public:
  static void init();
  static void executeWithBrownianJitter(void (*criticalTask)(void));
  static void executeWithBrownianJitter(void (*criticalTask)(void *), void *context);
  static uint32_t jitterMicros();
  static uint32_t brownianEntropy();
  static uint32_t harvestThermodynamicEntropy();
};

/** Wrap mission-critical call sites to shatter phase-locking side channels. */
#define OMEGA_BROWNIAN_SHIELD(task) StochasticShield::executeWithBrownianJitter(task)

inline void stochasticShieldInit() { StochasticShield::init(); }
