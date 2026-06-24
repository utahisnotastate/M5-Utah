#include "AmnesiaKernel.h"

#include "TimeTravelJournal.h"

#include <M5Unified.h>
#include <esp_heap_caps.h>
#include <esp_random.h>
#include <esp_system.h>
#include <cmath>
#include <cstring>

namespace {

constexpr size_t kDefaultMatrixBytes = 64 * 1024;
constexpr float kTamperAccelThreshold = 1.5f;
constexpr float kAnchorDriftThreshold = 0.45f;

void entropyScrub(uint8_t *buffer, size_t len) {
  if (buffer == nullptr || len == 0) {
    return;
  }
  for (size_t offset = 0; offset < len; offset += sizeof(uint32_t)) {
    const uint32_t noise = esp_random();
    const size_t chunk = (len - offset) >= sizeof(uint32_t) ? sizeof(uint32_t) : (len - offset);
    memcpy(buffer + offset, &noise, chunk);
  }
}

}  // namespace

AmnesiaKernel &AmnesiaKernel::instance() {
  static AmnesiaKernel kernel;
  return kernel;
}

bool AmnesiaKernel::ensureBuffer() {
  if (volatile_matrix_ != nullptr) {
    return true;
  }
  matrix_capacity_ = kDefaultMatrixBytes;
  volatile_matrix_ =
      static_cast<uint8_t *>(heap_caps_malloc(matrix_capacity_, MALLOC_CAP_SPIRAM | MALLOC_CAP_8BIT));
  if (volatile_matrix_ != nullptr) {
    requires_psram_ = true;
    return true;
  }

  if (requires_psram_) {
    return false;
  }

  matrix_capacity_ = 16 * 1024;
  volatile_matrix_ =
      static_cast<uint8_t *>(heap_caps_malloc(matrix_capacity_, MALLOC_CAP_INTERNAL | MALLOC_CAP_8BIT));
  return volatile_matrix_ != nullptr;
}

void AmnesiaKernel::init() {
  if (!ensureBuffer()) {
    Serial.println("[AMNESIA] Volatile matrix unavailable — ephemeral vault disabled.");
    return;
  }
  memset(volatile_matrix_, 0, matrix_capacity_);
  payload_len_ = 0;
  timeTravelRecord("amnesia:init");
  Serial.printf("[AMNESIA] Ephemeral instruction matrix online (%u bytes volatile).\n",
                static_cast<unsigned>(matrix_capacity_));
}

const uint8_t *AmnesiaKernel::payloadBytes() const { return volatile_matrix_; }

bool AmnesiaKernel::storePayload(const uint8_t *payload, size_t len) {
  if (payload == nullptr || len == 0) {
    return false;
  }
  if (!ensureBuffer() || len > matrix_capacity_) {
    return false;
  }
  memcpy(volatile_matrix_, payload, len);
  if (len < matrix_capacity_) {
    memset(volatile_matrix_ + len, 0, matrix_capacity_ - len);
  }
  payload_len_ = len;
  timeTravelRecord("amnesia:payload_stored");
  return true;
}

void AmnesiaKernel::verifyGeographicalAnchor(float accelX, float accelY, float accelZ) {
  if (!hasPayload()) {
    return;
  }

  if (!anchor_set_) {
    anchor_x_ = accelX;
    anchor_y_ = accelY;
    anchor_z_ = accelZ;
    anchor_set_ = true;
    return;
  }

  const float dx = accelX - anchor_x_;
  const float dy = accelY - anchor_y_;
  const float dz = accelZ - anchor_z_;
  const float drift = dx * dx + dy * dy + dz * dz;

  if (fabsf(accelX) > kTamperAccelThreshold || fabsf(accelY) > kTamperAccelThreshold ||
      fabsf(accelZ) > kTamperAccelThreshold || drift > kAnchorDriftThreshold) {
    panicWipe("geographical_anchor_breach");
  }
}

void AmnesiaKernel::wipePayload() {
  if (volatile_matrix_ == nullptr) {
    payload_len_ = 0;
    return;
  }
  entropyScrub(volatile_matrix_, matrix_capacity_);
  payload_len_ = 0;
  anchor_set_ = false;
  timeTravelRecord("amnesia:payload_wiped");
}

void AmnesiaKernel::panicWipe(const char *reason) {
  if (volatile_matrix_ != nullptr) {
    entropyScrub(volatile_matrix_, matrix_capacity_);
    memset(volatile_matrix_, 0xFF, matrix_capacity_);
    memset(volatile_matrix_, 0x00, matrix_capacity_);
    heap_caps_free(volatile_matrix_);
    volatile_matrix_ = nullptr;
  }
  payload_len_ = 0;
  matrix_capacity_ = 0;
  anchor_set_ = false;
  timeTravelRecord("amnesia:panic_wipe");
  Serial.printf("[AMNESIA] Panic wipe triggered (%s).\n", reason != nullptr ? reason : "unknown");
  esp_restart();
}
