#pragma once

#include <stddef.h>
#include <stdint.h>

constexpr int kM5KernelCoreProtocol = 0;
constexpr int kM5KernelCoreApplication = 1;

class M5Kernel {
 public:
  static void start();
  static void shutdown();
  static bool isRunning();
  static uint32_t processedFrameCount();
  static uint32_t orchestrationTicks();

  static bool dispatchPipeFrame(uint8_t kind, uint8_t *payload, size_t payloadLen);
};

bool m5KernelDrainPipeFrame();
void m5KernelApplicationCoreTask(void *param);
