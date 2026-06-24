#pragma once

#include <stddef.h>
#include <stdint.h>

/** Retinal bypass spatial UI — backlight off, magnetic flux projection from luminance buffer. */
class SpatialUI {
public:
  static void initRetinalProjection();
  static void projectHolographicFrame(const uint8_t *videoBuffer, size_t bufferSize);
  static bool isActive() { return active_; }
  static uint32_t framesProjected() { return frames_projected_; }

private:
  static int mapLuminosityToFlux(uint8_t pixel);
  static bool active_;
  static uint32_t frames_projected_;
};

inline void spatialUIInit() { SpatialUI::initRetinalProjection(); }
