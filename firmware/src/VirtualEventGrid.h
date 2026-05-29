#pragma once

#include "TelemetryFilter.h"

#include <ArduinoJson.h>

/** 1D EKF step — alias for TelemetryKalmanFilter with IMU-tuned defaults. */
using StochasticTelemetryFilter = TelemetryKalmanFilter;

constexpr float kImuFilterProcessVariance = 0.015f;
constexpr float kImuFilterMeasurementVariance = 0.550f;
constexpr float kImuTiltEventThreshold = 0.8f;

StochasticTelemetryFilter &imuStochasticFilter();

/** Emit Kalman-filtered virtual event on Fluxwire (Core 1 safe, static JSON). */
void broadcastPristineEvent(const char *eventType, float filteredMagnitude, int sourcePin);

/** Sample IMU accel, filter noise, emit imu_tilt_event when above threshold. */
void scanFilteredImuVirtualEvents();
