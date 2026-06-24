#include "GenesisProtocol.h"

#include "TimeTravelJournal.h"

#include <Arduino.h>
#include <esp_system.h>
#include <rom/rtc.h>

namespace {

RTC_DATA_ATTR uint32_t rtc_generation = 0;

}  // namespace

bool GenesisProtocol::genesis_boot_ = false;
uint32_t GenesisProtocol::generation_ = 0;

void GenesisProtocol::anchorRealityBoot() {
  const esp_reset_reason_t reason = esp_reset_reason();
  genesis_boot_ = (reason == ESP_RST_POWERON);
  if (genesis_boot_) {
    rtc_generation++;
  }
  generation_ = rtc_generation;
  timeTravelRecord("genesis:anchor");
  Serial.printf("[GENESIS] Sovereign reality anchor gen=%u reason=%d\n", generation_,
                static_cast<int>(reason));
}
