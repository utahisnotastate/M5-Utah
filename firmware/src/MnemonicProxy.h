#pragma once

#include <stddef.h>
#include <stdint.h>

/** Opportunistic ambient IoT mesh compute dispatch (local ESP-NOW tasks). */
class MnemonicProxy {
public:
  static constexpr uint8_t kMagic = 0x4D;

  struct __attribute__((packed)) ParasiticPayload {
    uint8_t magic;
    uint8_t task_id;
    float tensor_chunk[8];
  };

  static void init();
  static void initiateHiveScan();
  static bool dispatchComputeTask(const float *matrix, size_t size);
  static void recordPromiscuousMac(const uint8_t *mac);
  static int discoveredNodes() { return discovered_nodes_; }
  static uint32_t dispatchCount() { return dispatch_count_; }

private:
  static constexpr int kMaxAmbientNodes = 4;

  static uint8_t ambient_nodes_[kMaxAmbientNodes][6];
  static int discovered_nodes_;
  static uint32_t dispatch_count_;
};

inline void mnemonicProxyInit() { MnemonicProxy::init(); }
