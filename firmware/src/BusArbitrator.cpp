#include "BusArbitrator.h"

#include <ArduinoJson.h>
#include <cstring>

BusArbitrator &globalBusArbitrator() {
  static BusArbitrator arbitrator;
  return arbitrator;
}

void BusArbitrator::initializeArbitrator() {
  busMutex_ = xSemaphoreCreateMutex();
  activeSlotsCount_ = 0;
  rejectedCount_ = 0;
  for (int i = 0; i < kMaxArbitratedSlots; i++) {
    slots_[i].unitId = -1;
    slots_[i].allowedWindowMs = 0;
    slots_[i].lastExecutionTimestamp = 0;
    slots_[i].active = false;
  }
  Serial.println("[ARBITRATOR] Shared peripheral bus containment matrix active.");
}

int BusArbitrator::findSlot(int unitId) const {
  for (int i = 0; i < activeSlotsCount_; i++) {
    if (slots_[i].active && slots_[i].unitId == unitId) {
      return i;
    }
  }
  return -1;
}

void BusArbitrator::registerUnitSlot(int unitId, uint32_t windowMs) {
  if (unitId < 0 || windowMs == 0) {
    return;
  }

  const int existing = findSlot(unitId);
  if (existing >= 0) {
    slots_[existing].allowedWindowMs = windowMs;
    return;
  }

  if (activeSlotsCount_ >= kMaxArbitratedSlots) {
    Serial.println("[ARBITRATOR] Slot table full — cannot register additional bus unit.");
    return;
  }

  slots_[activeSlotsCount_] = {unitId, windowMs, 0, true};
  activeSlotsCount_++;
  Serial.printf("[ARBITRATOR] Registered unit %d with TDMA window %u ms\n", unitId, windowMs);
}

bool BusArbitrator::executeSafeBusTransaction(int unitId, BusActionFn busAction, void *context) {
  if (busAction == nullptr || busMutex_ == nullptr) {
    return false;
  }

  const int slotIndex = findSlot(unitId);
  if (slotIndex < 0) {
    if (xSemaphoreTake(busMutex_, pdMS_TO_TICKS(10)) == pdTRUE) {
      busAction(context);
      xSemaphoreGive(busMutex_);
      return true;
    }
    rejectedCount_++;
    return false;
  }

  const uint32_t currentTick = millis();
  ArbitratedSlot &slot = slots_[slotIndex];
  if (currentTick - slot.lastExecutionTimestamp < slot.allowedWindowMs) {
    rejectedCount_++;
    return false;
  }

  if (xSemaphoreTake(busMutex_, pdMS_TO_TICKS(10)) == pdTRUE) {
    busAction(context);
    xSemaphoreGive(busMutex_);
    slot.lastExecutionTimestamp = currentTick;
    return true;
  }

  rejectedCount_++;
  return false;
}

int BusArbitrator::activeSlotCount() const { return activeSlotsCount_; }

uint32_t BusArbitrator::rejectedTransactions() const { return rejectedCount_; }

bool isSharedBusProtocol(const char *protocolType) {
  if (protocolType == nullptr) {
    return false;
  }
  return strcmp(protocolType, "I2C") == 0 || strcmp(protocolType, "i2c") == 0 ||
         strcmp(protocolType, "SPI") == 0 || strcmp(protocolType, "spi") == 0;
}

int deriveBusUnitId(const char *unitName) {
  if (unitName == nullptr) {
    return 0;
  }
  unsigned hash = 0;
  for (const char *p = unitName; *p != '\0'; ++p) {
    hash = hash * 31u + static_cast<unsigned>(*p);
  }
  return static_cast<int>((hash % 900u) + 100u);
}

uint32_t defaultBusWindowMs(JsonObjectConst unit, int frequencyHz) {
  const uint32_t configured = unit["bus_arbitration_window_ms"] | 0;
  if (configured > 0) {
    return configured;
  }
  if (frequencyHz <= 0) {
    return 50;
  }
  uint32_t windowMs = static_cast<uint32_t>(1000 / frequencyHz);
  return windowMs < 10 ? 10 : windowMs;
}
