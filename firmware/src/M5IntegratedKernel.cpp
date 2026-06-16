#include "M5IntegratedKernel.h"

#include "ImmortalDiscovery.h"
#include "JumpKernel.h"
#include "OtaRollbackFence.h"
#include "SystemHealthHarvester.h"
#include "VectorFence.h"
#include "registry_runtime.h"

/**
 * Unified m5-kernel boot — Central Processing Registry Core entry point.
 *
 * Wires registry runtime, virtual handle pool, gatekeeper, bus arbitrator,
 * and dual-core CrossCorePipe + M5Kernel orchestration loop.
 * Do NOT replace with ad-hoc Serial.readBytes tasks in main.cpp.
 */
void m5IntegratedKernelBoot() {
  registryRuntimeInit();
  otaRollbackFenceInit();
  jumpKernelInitDefaults();
  vectorFenceInit();
  systemHealthHarvesterInit();
  immortalDiscoveryInit();
  M5Kernel::start();
}

bool m5IntegratedKernelIsActive() { return M5Kernel::isRunning(); }
