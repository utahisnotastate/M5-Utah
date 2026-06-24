#include "SovereignEdge.h"

#include <M5Unified.h>

#include "AcousticMask.h"
#include "MatrixCompute.h"
#include "MeshStateMirror.h"
#include "RealitySubstrate.h"
#include "SwarmSoul.h"

namespace {

constexpr uint32_t kSwarmBroadcastIntervalMs = 10;
uint32_t g_lastSwarmBroadcastMs = 0;

}  // namespace

void sovereignEdgeInit() {
  swarmSoulInit();
  acousticMaskInit();
}

void sovereignEdgeTick(uint32_t orchestrationTick, uint32_t processedFrames) {
  float imuX = 0.0f;
  float imuY = 0.0f;
  float imuZ = 0.0f;
  float tensorScore = 0.0f;

  if (M5.Imu.isEnabled()) {
    M5.Imu.update();
    auto imu = M5.Imu.getImuData();
    imuX = imu.accel.x;
    imuY = imu.accel.y;
    imuZ = imu.accel.z;
  }

  const float telematic[4] = {imuX, imuY, imuZ, static_cast<float>(orchestrationTick & 0xFF)};
  tensorScore = MatrixCompute::evaluateTelematicVector(telematic, 4);

  if (MeshStateMirror::instance().isActive()) {
    const uint32_t now = millis();
    if (now - g_lastSwarmBroadcastMs >= kSwarmBroadcastIntervalMs) {
      g_lastSwarmBroadcastMs = now;
      SwarmSoul::serializeCurrentState(orchestrationTick, processedFrames,
                                       static_cast<uint32_t>(tensorScore * 1000.0f), tensorScore);
    }
  }
  realitySubstrateTick(orchestrationTick, processedFrames);
}
