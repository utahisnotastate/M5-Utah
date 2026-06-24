#pragma once

#include <stdint.h>

/** RTC-surviving crash marker and resurrection telemetry. */
class LazarusDaemon {
public:
  static void init();
  static void heartbeat(uint32_t orchestrationTick);
  static bool resurrected() { return resurrected_; }
  static uint32_t bootCount() { return boot_count_; }
  static uint32_t lastSurvivingTick() { return last_surviving_tick_; }

private:
  static bool resurrected_;
  static uint32_t boot_count_;
  static uint32_t last_surviving_tick_;
};

inline void lazarusDaemonInit() { LazarusDaemon::init(); }

inline void lazarusDaemonHeartbeat(uint32_t orchestrationTick) {
  LazarusDaemon::heartbeat(orchestrationTick);
}
