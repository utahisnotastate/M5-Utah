#pragma once

#include <ArduinoJson.h>

#include "StateForker.h"

void registryRuntimeInit();
void registryHotReload(const JsonObjectConst &registryRoot);
void registrySupervisorTick();
void registryRespondCapabilities(JsonObject out);
void registryApplyBinwireUnit(const char *unitName, uint8_t pin, uint16_t frequencyHz,
                              uint32_t sequenceId);
void registryCaptureStableSnapshot(const char *unitName, const UnitTaskConfig *cfg);
void registryRevertUnitToStable(const char *unitName);
