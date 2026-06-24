#pragma once

#include <stdint.h>

/** Phyto-computing bus — organic non-linear activation via DAC/ADC probes. */
class BiosymmetricBus {
public:
  static void initOrganicSubstrate();
  static float applyOrganicActivation(float latentTensorValue);
  static bool isActive() { return active_; }
  static uint32_t activationCount() { return activation_count_; }

private:
  static int mapTensorToVoltage(float tensor);
  static float mapVoltageToTensor(int voltage);
  static bool active_;
  static uint32_t activation_count_;
};

inline void biosymmetricBusInit() { BiosymmetricBus::initOrganicSubstrate(); }
