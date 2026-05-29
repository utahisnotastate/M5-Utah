#pragma once

#include <ArduinoJson.h>

class DynamicMultiplexer {
 public:
  static void configureProcessorTopology(JsonObjectConst unit);
  static void resetAll();
};
