#include "MeshStateMirror.h"

#include "TimeTravelJournal.h"

#include <M5Unified.h>
#include <WiFi.h>
#include <cstring>
#include <esp_now.h>
#include <esp_sleep.h>

namespace {

constexpr uint32_t kBroadcastIntervalMs = 10;
constexpr uint32_t kFatalHeapBytes = 12 * 1024;
constexpr uint8_t kBroadcastAddress[] = {0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF};

MeshStateMirror *g_mirror = nullptr;

void onEspNowReceive(const uint8_t *mac, const uint8_t *data, int len) {
  (void)mac;
  if (g_mirror != nullptr) {
    g_mirror->receivePeerState(data, len);
  }
}

}  // namespace

MeshStateMirror &MeshStateMirror::instance() {
  static MeshStateMirror mirror;
  g_mirror = &mirror;
  return mirror;
}

void MeshStateMirror::refreshChecksum(MeshStateVector *state) const {
  if (state == nullptr) {
    return;
  }
  uint8_t rolling = 0x5A;
  const uint8_t *bytes = reinterpret_cast<const uint8_t *>(state);
  const size_t payloadLen = sizeof(MeshStateVector) - sizeof(state->execution_checksum);
  for (size_t i = 0; i < payloadLen; ++i) {
    rolling = static_cast<uint8_t>(rolling ^ bytes[i] ^ static_cast<uint8_t>(i * 17));
  }
  for (size_t i = 0; i < sizeof(state->execution_checksum); ++i) {
    state->execution_checksum[i] = static_cast<uint8_t>(rolling + i * 31);
    rolling = static_cast<uint8_t>(rolling ^ state->execution_checksum[i]);
  }
}

bool MeshStateMirror::verifyChecksum(const MeshStateVector &state) const {
  uint8_t observed[32];
  memcpy(observed, state.execution_checksum, sizeof(observed));
  MeshStateVector scratch = state;
  memset(scratch.execution_checksum, 0, sizeof(scratch.execution_checksum));
  refreshChecksum(&scratch);
  return memcmp(observed, scratch.execution_checksum, sizeof(observed)) == 0;
}

void MeshStateMirror::triggerSuicideHandoff(const char *reason) {
  if (!active_) {
    return;
  }

  refreshChecksum(&local_state_);
  esp_now_send(kBroadcastAddress, reinterpret_cast<uint8_t *>(&local_state_), sizeof(local_state_));
  suicide_handoffs_++;
  timeTravelRecord("mesh_mirror:suicide_handoff");
  Serial.printf("[MESH MIRROR] DeepSleep suicide handoff (%s) tick=%u\n",
                reason != nullptr ? reason : "unknown", local_state_.orchestration_tick);

  esp_deep_sleep_start();
}

void MeshStateMirror::evaluateFatalAnomaly(uint32_t freeHeapBytes) {
  if (!active_ || freeHeapBytes >= kFatalHeapBytes) {
    return;
  }
  triggerSuicideHandoff("heap_corruption_pressure");
}

void MeshStateMirror::initSwarm() {
  if (active_) {
    return;
  }

  session_id_ = esp_random();
  WiFi.mode(WIFI_STA);
  WiFi.disconnect(false, true);

  if (esp_now_init() != ESP_OK) {
    Serial.println("[MESH MIRROR] ESP-NOW unavailable — local-only execution.");
    return;
  }

  esp_now_register_recv_cb(onEspNowReceive);

  esp_now_peer_info_t peerInfo = {};
  memcpy(peerInfo.peer_addr, kBroadcastAddress, sizeof(kBroadcastAddress));
  peerInfo.channel = 0;
  peerInfo.encrypt = false;
  if (esp_now_add_peer(&peerInfo) != ESP_OK) {
    Serial.println("[MESH MIRROR] Peer registration failed.");
    esp_now_deinit();
    return;
  }

  active_ = true;
  timeTravelRecord("mesh_mirror:swarm_online");
  Serial.println("[MESH MIRROR] Byzantine state mirroring armed (10ms cadence).");
}

void MeshStateMirror::tick(uint32_t orchestrationTick, uint32_t processedFrames, float imuX,
                           float imuY) {
  local_state_.session_id = session_id_;
  local_state_.orchestration_tick = orchestrationTick;
  local_state_.processed_frames = processedFrames;
  local_state_.thermodynamic_variable_1 = imuX;
  local_state_.thermodynamic_variable_2 = imuY;
  refreshChecksum(&local_state_);

  if (!active_) {
    return;
  }

  const uint32_t now = millis();
  if (now - last_broadcast_ms_ < kBroadcastIntervalMs) {
    return;
  }
  last_broadcast_ms_ = now;

  if (esp_now_send(kBroadcastAddress, reinterpret_cast<uint8_t *>(&local_state_),
                   sizeof(local_state_)) == ESP_OK) {
    timeTravelRecord("mesh_mirror:broadcast");
  }
}

void MeshStateMirror::receivePeerState(const uint8_t *data, int len) {
  if (data == nullptr || len != static_cast<int>(sizeof(MeshStateVector))) {
    return;
  }

  MeshStateVector incoming{};
  memcpy(&incoming, data, sizeof(incoming));
  if (!verifyChecksum(incoming)) {
    timeTravelRecord("mesh_mirror:checksum_reject");
    return;
  }

  peer_state_ = incoming;
  peer_updates_++;

  if (peer_state_.session_id != session_id_ &&
      peer_state_.orchestration_tick > local_state_.orchestration_tick) {
    local_state_ = peer_state_;
    timeTravelRecord("mesh_mirror:failover_adopt");
    Serial.printf("[MESH MIRROR] Adopted peer state tick=%u frames=%u\n",
                  peer_state_.orchestration_tick, peer_state_.processed_frames);
  }
}
