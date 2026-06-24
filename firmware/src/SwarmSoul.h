#pragma once

#include <stdint.h>

/** Asynchronous swarm conslation — ExecutionFrame sync over ESP-NOW (shared radio bus). */
class SwarmSoul {
public:
  struct __attribute__((packed)) ExecutionFrame {
    uint32_t state_sequence_id;
    uint32_t logical_instruction_pointer;
    uint32_t hardware_register_state[4];
    float environmental_noise_floor;
    uint16_t operational_checksum;
  };

  static void initFrameState();
  static void serializeCurrentState(uint32_t activeIp, uint32_t r0, uint32_t r1, float ambientNoise);
  static void onPeerSynchronizeEvent(const uint8_t *sourceMac, const uint8_t *payload, int len);
  static bool verifyFrame(const ExecutionFrame &frame);
  static uint32_t peerAdoptions() { return peer_adoptions_; }
  static const ExecutionFrame &localFrame() { return local_frame_; }

private:
  static void refreshChecksum(ExecutionFrame *frame);
  static uint16_t computeChecksum(const ExecutionFrame &frame);

  static ExecutionFrame local_frame_;
  static ExecutionFrame peer_frame_;
  static uint32_t peer_adoptions_;
};

inline void swarmSoulInit() { SwarmSoul::initFrameState(); }
