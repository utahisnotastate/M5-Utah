#pragma once

#include <stdint.h>

void telemetryHealthRecordFastPath(uint8_t unitId, uint8_t pin);
uint8_t telemetryHealthActiveUnit();
uint8_t telemetryHealthActivePin();
uint32_t telemetryHealthLastLoopJitterMs();
void telemetryHealthUpdateOrchestrationJitter();
