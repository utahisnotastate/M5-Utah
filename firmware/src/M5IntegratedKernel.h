#pragma once

/**
 * m5-kernel — Integrated Asymmetric Dual-Core Processing Runtime
 *
 * Maps the production module graph (do NOT duplicate in main.cpp):
 *
 * | Zone | Core | Module | Responsibility |
 * |------|------|--------|----------------|
 * | Protocol Engine | 0 | CrossCorePipe | Serial ingest, ##/#P/#M/0xDE demux, ring push |
 * | Orchestration Engine | 1 | M5Kernel | Ring drain, intent dispatch, telemetry |
 * | Priority Gatekeeper | 1 | PriorityGatekeeper | Proactive boost + mutex (anti inversion) |
 * | Bus Arbitrator | 1 | BusArbitrator | TDMA I2C/SPI hot-swap windows |
 * | Handle Memory | 1 | HandleMemoryManager | Virtual handle pool, compaction |
 * | Resource Orchestrator | 1 | ResourceOrchestrator | Pressure-based deferral |
 *
 * Boot: registryRuntimeInit() → M5Kernel::start() → loop() suspended.
 * Host: HostSchedulerCompiler.apply_to_intent() before IntentController.send_intent().
 */

#include "BusArbitrator.h"
#include "CrossCorePipe.h"
#include "DualCoreHarness.h"
#include "HandleMemory.h"
#include "M5Kernel.h"
#include "PriorityGatekeeper.h"
#include "ResourceOrchestrator.h"
#include "RPPDecoder.h"

/** Boot the integrated dual-core m5-kernel (registry + CrossCorePipe + M5Kernel). */
void m5IntegratedKernelBoot();

/** True after m5IntegratedKernelBoot() has started Core 0/1 tasks. */
bool m5IntegratedKernelIsActive();

inline RingbufHandle_t m5KernelIntentRingBuffer() {
  return dualCoreFastPathQueueHandle();
}

inline bool m5KernelIsRunning() { return M5Kernel::isRunning(); }
