#pragma once

#include <stdint.h>

struct __attribute__((packed)) DiagnosticReportFrame {
  uint8_t unitId;
  uint32_t remainingHeapBytes;
  uint8_t measuredTaskJitterMs;
};

constexpr uint32_t kHealthVitalsReportIntervalMs = 1000;

/** Streams compact binary health vitals for host closed-loop remediation. */
class SystemHealthHarvester {
 public:
  void streamSystemVitals(uint8_t activeUnitId);
};

void systemHealthHarvesterInit();
SystemHealthHarvester &globalHealthHarvester();
