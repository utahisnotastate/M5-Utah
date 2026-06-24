#include "OmegaDefense.h"

#include <M5Unified.h>

#include "AmnesiaKernel.h"
#include "ChronoScheduler.h"
#include "LazarusDaemon.h"
#include "MeshStateMirror.h"
#include "StochasticShield.h"
#include "TensorVoidLinkage.h"

void omegaDefenseInit() {
  stochasticShieldInit();
  lazarusDaemonInit();
  amnesiaKernelInit();
  meshStateMirrorInit();
  chronoSchedulerInit();
}

void omegaDefenseTick(uint32_t orchestrationTick, uint32_t processedFrames) {
  lazarusDaemonHeartbeat(orchestrationTick);

  const uint32_t freeHeap = ESP.getFreeHeap();
  MeshStateMirror::instance().evaluateFatalAnomaly(freeHeap);

  float imuX = 0.0f;
  float imuY = 0.0f;
  float imuZ = 0.0f;
  if (M5.Imu.isEnabled()) {
    M5.Imu.update();
    auto imu = M5.Imu.getImuData();
    imuX = imu.accel.x;
    imuY = imu.accel.y;
    imuZ = imu.accel.z;
    amnesiaKernelVerifyAnchor(imuX, imuY, imuZ);
  }

  meshStateMirrorTick(orchestrationTick, processedFrames, imuX, imuY);

  const float sensor[3] = {imuX, imuY, imuZ};
  tensorVoidScore(sensor, 3);
}
