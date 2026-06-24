#pragma once

#include <stddef.h>
#include <stdint.h>

/** Ephemeral PSRAM payload vault — wiped on tamper or power loss. */
class AmnesiaKernel {
public:
  static AmnesiaKernel &instance();

  void init();
  bool storePayload(const uint8_t *payload, size_t len);
  bool hasPayload() const { return payload_len_ > 0; }
  size_t payloadLength() const { return payload_len_; }
  const uint8_t *payloadBytes() const;
  void verifyGeographicalAnchor(float accelX, float accelY, float accelZ);
  void panicWipe(const char *reason);
  void wipePayload();
  bool requiresPsram() const { return requires_psram_; }

private:
  AmnesiaKernel() = default;
  bool ensureBuffer();

  uint8_t *volatile_matrix_ = nullptr;
  size_t matrix_capacity_ = 0;
  size_t payload_len_ = 0;
  float anchor_x_ = 0.0f;
  float anchor_y_ = 0.0f;
  float anchor_z_ = 0.0f;
  bool anchor_set_ = false;
  bool requires_psram_ = false;
};

inline void amnesiaKernelInit() { AmnesiaKernel::instance().init(); }

inline void amnesiaKernelVerifyAnchor(float accelX, float accelY, float accelZ) {
  AmnesiaKernel::instance().verifyGeographicalAnchor(accelX, accelY, accelZ);
}
