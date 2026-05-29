#include "VectorTelemetry.h"

#include <cstring>

VectorTelemetryBuilder &VectorTelemetryBuilder::instance() {
  static VectorTelemetryBuilder builder;
  return builder;
}

VectorTelemetryBuilder &vectorTelemetry() { return VectorTelemetryBuilder::instance(); }

void VectorTelemetryBuilder::setNodeId(const char *nodeId) {
  if (nodeId == nullptr || nodeId[0] == '\0') {
    return;
  }
  strncpy(hardwareNodeId_, nodeId, sizeof(hardwareNodeId_) - 1);
}

void VectorTelemetryBuilder::applyHostVectorSync(JsonObjectConst syncVector) {
  for (JsonPairConst kv : syncVector) {
    if (strcmp(kv.key().c_str(), "android_host_node") == 0) {
      hostLogicalSequence_ = kv.value().as<uint32_t>();
    }
  }
}

void VectorTelemetryBuilder::attachToTelemetry(JsonObject doc, int activeUnitId) {
  localLogicalSequence_++;

  doc["sender_id"] = hardwareNodeId_;
  if (activeUnitId > 0) {
    doc["unit_id"] = activeUnitId;
  }

  JsonObject vectors = doc["vector_clocks"].to<JsonObject>();
  vectors[hardwareNodeId_] = localLogicalSequence_;
  vectors["android_host_node"] = hostLogicalSequence_;
}

void VectorTelemetryBuilder::attachToEvent(JsonObject doc) {
  localLogicalSequence_++;
  doc["sender_id"] = hardwareNodeId_;
  JsonObject vectors = doc["vector_clocks"].to<JsonObject>();
  vectors[hardwareNodeId_] = localLogicalSequence_;
  vectors["android_host_node"] = hostLogicalSequence_;
}

uint32_t VectorTelemetryBuilder::localSequence() const { return localLogicalSequence_; }
