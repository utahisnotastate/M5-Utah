#pragma once

#include <stdint.h>

struct MeshStateVector {
  uint32_t session_id;
  uint32_t orchestration_tick;
  uint32_t processed_frames;
  float thermodynamic_variable_1;
  float thermodynamic_variable_2;
  uint8_t execution_checksum[32];
};

class MeshStateMirror {
public:
  static MeshStateMirror &instance();

  void initSwarm();
  void tick(uint32_t orchestrationTick, uint32_t processedFrames, float imuX, float imuY);
  void receivePeerState(const uint8_t *data, int len);
  bool verifyChecksum(const MeshStateVector &state) const;
  void evaluateFatalAnomaly(uint32_t freeHeapBytes);
  void triggerSuicideHandoff(const char *reason);
  bool isActive() const { return active_; }
  uint32_t peerUpdates() const { return peer_updates_; }
  uint32_t suicideHandoffs() const { return suicide_handoffs_; }
  const MeshStateVector &localState() const { return local_state_; }
  const MeshStateVector &lastPeerState() const { return peer_state_; }

private:
  MeshStateMirror() = default;
  void refreshChecksum(MeshStateVector *state) const;

  bool active_ = false;
  uint32_t session_id_ = 0;
  uint32_t peer_updates_ = 0;
  uint32_t suicide_handoffs_ = 0;
  uint32_t last_broadcast_ms_ = 0;
  MeshStateVector local_state_{};
  MeshStateVector peer_state_{};
};

inline void meshStateMirrorInit() { MeshStateMirror::instance().initSwarm(); }

inline void meshStateMirrorTick(uint32_t orchestrationTick, uint32_t processedFrames, float imuX,
                                float imuY) {
  MeshStateMirror::instance().tick(orchestrationTick, processedFrames, imuX, imuY);
}
