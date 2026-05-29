#pragma once

class TelemetryKalmanFilter {
 public:
  explicit TelemetryKalmanFilter(float processVariance = 0.022f, float measurementVariance = 0.618f)
      : q_(processVariance), r_(measurementVariance), p_(1.0f), x_(0.0f), k_(0.0f) {}

  float computeFilteredMetric(float rawMeasurement) {
    k_ = (p_ + q_) / (p_ + q_ + r_);
    x_ = x_ + k_ * (rawMeasurement - x_);
    p_ = (1.0f - k_) * (p_ + q_);
    return x_;
  }

  void reset(float initialState = 0.0f) {
    p_ = 1.0f;
    x_ = initialState;
    k_ = 0.0f;
  }

  float estimate() const { return x_; }

 private:
  float q_;
  float r_;
  float p_;
  float x_;
  float k_;
};

class TelemetryFilterBank {
 public:
  TelemetryKalmanFilter accelX;
  TelemetryKalmanFilter accelY;
  TelemetryKalmanFilter accelZ;

  void filterImu(float rawX, float rawY, float rawZ, float &outX, float &outY, float &outZ) {
    outX = accelX.computeFilteredMetric(rawX);
    outY = accelY.computeFilteredMetric(rawY);
    outZ = accelZ.computeFilteredMetric(rawZ);
  }
};
