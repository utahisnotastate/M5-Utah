#pragma once

#include <stdint.h>

/** Omega-tier edge defense stack — boot + orchestration integration. */
void omegaDefenseInit();
void omegaDefenseTick(uint32_t orchestrationTick, uint32_t processedFrames);
