#include "RealitySubstrate.h"

#include <M5Unified.h>

#include "AkashicFileSystem.h"
#include "BiosymmetricBus.h"
#include "ChronoKinetic.h"
#include "CausalDebugger.h"
#include "EigenStateCompiler.h"
#include "GenesisProtocol.h"
#include "MatrixCompute.h"
#include "MnemonicProxy.h"
#include "SpatialUI.h"

namespace {

constexpr uint32_t kHiveScanIntervalMs = 30000;
uint32_t g_lastHiveScanMs = 0;

}  // namespace

void realitySubstrateInit() {
  genesisProtocolBoot();
  akashicFileSystemInit();
  chronoKineticInit();
  mnemonicProxyInit();
  causalDebuggerInit();
  eigenStateCompilerInit();
}

void realitySubstrateTick(uint32_t orchestrationTick, uint32_t processedFrames) {
  (void)processedFrames;
  AkashicFileSystem::maintainStandingWave();

  const uint32_t now = millis();
  if (now - g_lastHiveScanMs >= kHiveScanIntervalMs) {
    g_lastHiveScanMs = now;
    MnemonicProxy::initiateHiveScan();
  }

  float servoAngle = 0.0f;
  if (M5.Imu.isEnabled()) {
    M5.Imu.update();
    servoAngle = M5.Imu.getImuData().gyro.z;
  }
  const float organic =
      BiosymmetricBus::applyOrganicActivation(MatrixCompute::lastScore());
  ChronoKinetic::relaxToCoordinate(0, servoAngle, organic);

  const float matrix[8] = {organic, servoAngle, static_cast<float>(orchestrationTick),
                           MatrixCompute::lastScore(), 0.0f, 0.0f, 0.0f, 0.0f};
  MnemonicProxy::dispatchComputeTask(matrix, 8);
}
