#pragma once

#include <ArduinoJson.h>

class VectorTelemetryBuilder {
 public:
  static VectorTelemetryBuilder &instance();

  void setNodeId(const char *nodeId);
  void applyHostVectorSync(JsonObjectConst syncVector);
  void attachToTelemetry(JsonObject doc, int activeUnitId = 0);
  void attachToEvent(JsonObject doc);
  uint32_t localSequence() const;

 private:
  VectorTelemetryBuilder() = default;

  uint32_t localLogicalSequence_ = 0;
  char hardwareNodeId_[32] = "m5_node_01";
  uint32_t hostLogicalSequence_ = 0;
};

VectorTelemetryBuilder &vectorTelemetry();
