#include "SwarmSoul.h"

#include "TimeTravelJournal.h"

#include <Arduino.h>
#include <cstring>
#include <esp_now.h>

SwarmSoul::ExecutionFrame SwarmSoul::local_frame_{};
SwarmSoul::ExecutionFrame SwarmSoul::peer_frame_{};
uint32_t SwarmSoul::peer_adoptions_ = 0;

namespace {

constexpr uint8_t kBroadcastMac[] = {0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF};

}  // namespace

void SwarmSoul::initFrameState() {
  memset(&local_frame_, 0, sizeof(local_frame_));
  memset(&peer_frame_, 0, sizeof(peer_frame_));
  local_frame_.state_sequence_id = esp_random();
  timeTravelRecord("swarm_soul:frames_online");
}

uint16_t SwarmSoul::computeChecksum(const ExecutionFrame &frame) {
  uint16_t sum = 0;
  const uint8_t *bytes = reinterpret_cast<const uint8_t *>(&frame);
  const size_t payloadLen = sizeof(ExecutionFrame) - sizeof(frame.operational_checksum);
  for (size_t i = 0; i < payloadLen; ++i) {
    sum = static_cast<uint16_t>(sum + bytes[i]);
  }
  return sum;
}

void SwarmSoul::refreshChecksum(ExecutionFrame *frame) {
  if (frame == nullptr) {
    return;
  }
  frame->operational_checksum = computeChecksum(*frame);
}

bool SwarmSoul::verifyFrame(const ExecutionFrame &frame) {
  return computeChecksum(frame) == frame.operational_checksum;
}

void SwarmSoul::serializeCurrentState(uint32_t activeIp, uint32_t r0, uint32_t r1,
                                      float ambientNoise) {
  local_frame_.state_sequence_id++;
  local_frame_.logical_instruction_pointer = activeIp;
  local_frame_.hardware_register_state[0] = r0;
  local_frame_.hardware_register_state[1] = r1;
  local_frame_.hardware_register_state[2] = static_cast<uint32_t>(millis());
  local_frame_.hardware_register_state[3] = static_cast<uint32_t>(esp_random());
  local_frame_.environmental_noise_floor = ambientNoise;
  refreshChecksum(&local_frame_);

  esp_now_send(kBroadcastMac, reinterpret_cast<uint8_t *>(&local_frame_), sizeof(local_frame_));
}

void SwarmSoul::onPeerSynchronizeEvent(const uint8_t *sourceMac, const uint8_t *payload, int len) {
  (void)sourceMac;
  if (payload == nullptr || len != static_cast<int>(sizeof(ExecutionFrame))) {
    return;
  }

  ExecutionFrame inbound{};
  memcpy(&inbound, payload, sizeof(inbound));
  if (!verifyFrame(inbound)) {
    timeTravelRecord("swarm_soul:checksum_reject");
    return;
  }

  peer_frame_ = inbound;
  if (inbound.state_sequence_id > local_frame_.state_sequence_id) {
    local_frame_ = inbound;
    peer_adoptions_++;
    timeTravelRecord("swarm_soul:peer_adopt");
    Serial.printf("[SWARM SOUL] Adopted peer frame seq=%u ip=0x%08X\n",
                  inbound.state_sequence_id, inbound.logical_instruction_pointer);
  }
}
