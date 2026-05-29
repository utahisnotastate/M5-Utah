#pragma once

#include <ArduinoJson.h>

void registryRuntimeInit();
void registryHotReload(const JsonObjectConst &registryRoot);
void registrySupervisorTick();
void registryRespondCapabilities(JsonObject out);
