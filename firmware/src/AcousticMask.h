#pragma once

#include <stdint.h>

/** Declarative phonon-routing — I2S Brownian noise DMA mask (optional Core 0 task). */
class AcousticMask {
public:
  static bool initHardwareAudio();
  static void executeSaturatedStream();
  static bool isActive() { return active_; }
  static uint32_t framesWritten() { return frames_written_; }

private:
  static bool active_;
  static uint32_t frames_written_;
};

inline void acousticMaskInit() {
  if (AcousticMask::initHardwareAudio()) {
    extern void acousticMaskStartTask();
    acousticMaskStartTask();
  }
}
