#pragma once

#include <ArduinoJson.h>

class DynamicMultiplexer {
 public:
  static void configureProcessorTopology(JsonObjectConst unit, int busUnitId = 0,
                                       UBaseType_t callingPriority = 2);
  static void resetAll();
};
