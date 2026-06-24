#include "LazarusDaemon.h"

#include "TimeTravelJournal.h"

#include <Arduino.h>
#include <esp_system.h>
#include <rom/rtc.h>

namespace {

RTC_DATA_ATTR uint32_t rtc_boot_count = 0;
RTC_DATA_ATTR uint32_t rtc_last_tick = 0;
RTC_DATA_ATTR uint8_t rtc_crash_flag = 0;

const char *resetReasonLabel(esp_reset_reason_t reason) {
  switch (reason) {
    case ESP_RST_PANIC:
      return "panic";
    case ESP_RST_INT_WDT:
      return "interrupt_wdt";
    case ESP_RST_TASK_WDT:
      return "task_wdt";
    case ESP_RST_WDT:
      return "wdt";
    case ESP_RST_BROWNOUT:
      return "brownout";
    case ESP_RST_SW:
      return "software";
    case ESP_RST_POWERON:
      return "power_on";
    default:
      return "other";
  }
}

}  // namespace

bool LazarusDaemon::resurrected_ = false;
uint32_t LazarusDaemon::boot_count_ = 0;
uint32_t LazarusDaemon::last_surviving_tick_ = 0;

void LazarusDaemon::init() {
  const esp_reset_reason_t reason = esp_reset_reason();
  resurrected_ = rtc_crash_flag != 0 ||
                   reason == ESP_RST_PANIC || reason == ESP_RST_INT_WDT ||
                   reason == ESP_RST_TASK_WDT || reason == ESP_RST_WDT;

  rtc_boot_count++;
  boot_count_ = rtc_boot_count;
  last_surviving_tick_ = rtc_last_tick;
  rtc_crash_flag = 0;

  if (resurrected_) {
    timeTravelRecord("lazarus:resurrect");
    Serial.printf("[LAZARUS] Resurrected after %s — last tick=%u boot=%u\n",
                  resetReasonLabel(reason), rtc_last_tick, rtc_boot_count);
  } else {
    timeTravelRecord("lazarus:init");
    Serial.println("[LAZARUS] Hardware immortality daemon armed (RTC fast memory).");
  }
}

void LazarusDaemon::heartbeat(uint32_t orchestrationTick) {
  rtc_last_tick = orchestrationTick;
  last_surviving_tick_ = orchestrationTick;
}
