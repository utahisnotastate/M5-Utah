#pragma once

#include <stdint.h>

/** Sovereign edge tier — phonon mask, cache matrix, swarm conslation integration. */
void sovereignEdgeInit();
void sovereignEdgeTick(uint32_t orchestrationTick, uint32_t processedFrames);
