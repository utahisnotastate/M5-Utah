#pragma once

#include <stddef.h>
#include <stdint.h>

struct MemoryHandle {
  uint8_t *physicalAddress;
  size_t allocationSize;
  bool isLocked;
  bool inUse;
};

constexpr int kMaxMemoryHandles = 32;
constexpr size_t kHandleMemoryPoolBytes = 2048;

class HandleMemoryManager {
 public:
  void initializeMemoryPool();
  int allocateHandle(size_t size);
  int bindHandle(int handleId, size_t size);
  uint8_t *resolveHandle(int handleId);
  void setHandleLocked(int handleId, bool locked);
  void releaseHandle(int handleId);
  void compactMemoryPool();
  bool compactIfPressure(float thresholdRatio = 0.9f);
  size_t poolTop() const;
  size_t poolLimit() const;
  float fragmentationIndex() const;
  int activeHandleCount() const;

 private:
  MemoryHandle handleTable_[kMaxMemoryHandles] = {};
  uint8_t memoryPool_[kHandleMemoryPoolBytes] = {};
  size_t poolAllocatedTop_ = 0;

  int findFreeSlot() const;
  bool ensurePoolSpace(size_t size);
};

HandleMemoryManager &globalMemoryManager();
