#pragma once

#include <stdint.h>

/** Sovereign genesis boot anchor — RTC coherence marker on power-on. */
class GenesisProtocol {
public:
  static void anchorRealityBoot();
  static bool isGenesisBoot() { return genesis_boot_; }
  static uint32_t generation() { return generation_; }

private:
  static bool genesis_boot_;
  static uint32_t generation_;
};

inline void genesisProtocolBoot() { GenesisProtocol::anchorRealityBoot(); }
