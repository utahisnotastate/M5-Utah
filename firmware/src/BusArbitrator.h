#pragma once

#include <Arduino.h>
#include <ArduinoJson.h>
#include <freertos/FreeRTOS.h>
#include <freertos/semphr.h>
#include <stdint.h>

struct ArbitratedSlot {
  int unitId;
  uint32_t allowedWindowMs;
  uint32_t lastExecutionTimestamp;
  bool active;
};

using BusActionFn = void (*)(void *context);

constexpr int kMaxArbitratedSlots = 8;

class BusArbitrator {
 public:
  void initializeArbitrator();
  void registerUnitSlot(int unitId, uint32_t windowMs);
  bool executeSafeBusTransaction(int unitId, BusActionFn busAction, void *context);
  int activeSlotCount() const;
  uint32_t rejectedTransactions() const;

 private:
  ArbitratedSlot slots_[kMaxArbitratedSlots] = {};
  int activeSlotsCount_ = 0;
  SemaphoreHandle_t busMutex_ = nullptr;
  uint32_t rejectedCount_ = 0;

  int findSlot(int unitId) const;
};

BusArbitrator &globalBusArbitrator();

bool isSharedBusProtocol(const char *protocolType);
int deriveBusUnitId(const char *unitName);
uint32_t defaultBusWindowMs(JsonObjectConst unit, int frequencyHz);
