#include "HandleMemory.h"

#include "TimeTravelJournal.h"

#include <Arduino.h>
#include <cstring>

HandleMemoryManager &globalMemoryManager() {
  static HandleMemoryManager manager;
  return manager;
}

void HandleMemoryManager::initializeMemoryPool() {
  memset(memoryPool_, 0, sizeof(memoryPool_));
  poolAllocatedTop_ = 0;
  for (int i = 0; i < kMaxMemoryHandles; i++) {
    handleTable_[i].physicalAddress = nullptr;
    handleTable_[i].allocationSize = 0;
    handleTable_[i].isLocked = false;
    handleTable_[i].inUse = false;
  }
  Serial.println("[MEMORY] Virtual Handle Matrix initialized successfully.");
}

int HandleMemoryManager::findFreeSlot() const {
  for (int i = 0; i < kMaxMemoryHandles; i++) {
    if (!handleTable_[i].inUse) {
      return i;
    }
  }
  return -1;
}

bool HandleMemoryManager::ensurePoolSpace(size_t size) {
  if (poolAllocatedTop_ + size <= kHandleMemoryPoolBytes) {
    return true;
  }
  compactMemoryPool();
  return poolAllocatedTop_ + size <= kHandleMemoryPoolBytes;
}

int HandleMemoryManager::allocateHandle(size_t size) {
  if (size == 0 || size > kHandleMemoryPoolBytes) {
    return -1;
  }
  if (!ensurePoolSpace(size)) {
    return -1;
  }

  const int slot = findFreeSlot();
  if (slot < 0) {
    return -1;
  }

  handleTable_[slot].physicalAddress = &memoryPool_[poolAllocatedTop_];
  handleTable_[slot].allocationSize = size;
  handleTable_[slot].isLocked = false;
  handleTable_[slot].inUse = true;
  memset(handleTable_[slot].physicalAddress, 0, size);
  poolAllocatedTop_ += size;
  return slot;
}

int HandleMemoryManager::bindHandle(int handleId, size_t size) {
  if (handleId < 0 || handleId >= kMaxMemoryHandles || size == 0 ||
      size > kHandleMemoryPoolBytes) {
    return -1;
  }

  if (handleTable_[handleId].inUse) {
    if (handleTable_[handleId].isLocked) {
      return -1;
    }
    releaseHandle(handleId);
  }

  if (!ensurePoolSpace(size)) {
    return -1;
  }

  handleTable_[handleId].physicalAddress = &memoryPool_[poolAllocatedTop_];
  handleTable_[handleId].allocationSize = size;
  handleTable_[handleId].isLocked = false;
  handleTable_[handleId].inUse = true;
  memset(handleTable_[handleId].physicalAddress, 0, size);
  poolAllocatedTop_ += size;
  return handleId;
}

uint8_t *HandleMemoryManager::resolveHandle(int handleId) {
  if (handleId < 0 || handleId >= kMaxMemoryHandles || !handleTable_[handleId].inUse) {
    return nullptr;
  }
  return handleTable_[handleId].physicalAddress;
}

void HandleMemoryManager::setHandleLocked(int handleId, bool locked) {
  if (handleId < 0 || handleId >= kMaxMemoryHandles || !handleTable_[handleId].inUse) {
    return;
  }
  handleTable_[handleId].isLocked = locked;
}

void HandleMemoryManager::releaseHandle(int handleId) {
  if (handleId < 0 || handleId >= kMaxMemoryHandles || !handleTable_[handleId].inUse) {
    return;
  }
  handleTable_[handleId].physicalAddress = nullptr;
  handleTable_[handleId].allocationSize = 0;
  handleTable_[handleId].isLocked = false;
  handleTable_[handleId].inUse = false;
}

void HandleMemoryManager::compactMemoryPool() {
  Serial.println(
      "[COMPACTOR] Fragmented heap limit reached. Initiating speculative memory alignment "
      "shift...");
  size_t compactionWritePointer = 0;

  for (int i = 0; i < kMaxMemoryHandles; i++) {
    if (!handleTable_[i].inUse || handleTable_[i].physicalAddress == nullptr) {
      continue;
    }
    if (handleTable_[i].isLocked) {
      continue;
    }

    if (handleTable_[i].physicalAddress != &memoryPool_[compactionWritePointer]) {
      memmove(&memoryPool_[compactionWritePointer], handleTable_[i].physicalAddress,
              handleTable_[i].allocationSize);
      handleTable_[i].physicalAddress = &memoryPool_[compactionWritePointer];
    }
    compactionWritePointer += handleTable_[i].allocationSize;
  }

  poolAllocatedTop_ = compactionWritePointer;
  timeTravelRecord("memory:compact");
  Serial.printf("[SUCCESS] Heap compaction complete. Active Top: %u bytes\n",
                static_cast<unsigned>(poolAllocatedTop_));
}

bool HandleMemoryManager::compactIfPressure(float thresholdRatio) {
  if (kHandleMemoryPoolBytes == 0) {
    return false;
  }
  const float utilization =
      static_cast<float>(poolAllocatedTop_) / static_cast<float>(kHandleMemoryPoolBytes);
  if (utilization >= thresholdRatio) {
    compactMemoryPool();
    return true;
  }
  return false;
}

size_t HandleMemoryManager::poolTop() const { return poolAllocatedTop_; }

size_t HandleMemoryManager::poolLimit() const { return kHandleMemoryPoolBytes; }

float HandleMemoryManager::fragmentationIndex() const {
  if (poolAllocatedTop_ == 0) {
    return 0.0f;
  }
  size_t accounted = 0;
  for (int i = 0; i < kMaxMemoryHandles; i++) {
    if (handleTable_[i].inUse) {
      accounted += handleTable_[i].allocationSize;
    }
  }
  if (accounted >= poolAllocatedTop_) {
    return 0.0f;
  }
  return static_cast<float>(poolAllocatedTop_ - accounted) /
         static_cast<float>(poolAllocatedTop_);
}

int HandleMemoryManager::activeHandleCount() const {
  int count = 0;
  for (int i = 0; i < kMaxMemoryHandles; i++) {
    if (handleTable_[i].inUse) {
      count++;
    }
  }
  return count;
}
