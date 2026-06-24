#pragma once

#include <stdint.h>

/** Predictive micro-scheduler — pre-commits speculative tasks on a hyper-timer. */
class ChronoScheduler {
public:
  static ChronoScheduler &instance();

  void init();
  void injectFutureState(void (*task)(void), uint32_t expectedDeltaUs);
  uint32_t committedCount() const { return committed_count_; }
  void onHyperTick();

private:
  ChronoScheduler() = default;

  struct FutureStateNode {
    uint32_t simulated_timestamp_us = 0;
    void (*speculative_task)(void) = nullptr;
    bool is_committed = false;
  };

  FutureStateNode probability_matrix_[3]{};
  uint8_t current_vector_ = 0;
  uint32_t committed_count_ = 0;
};

inline void chronoSchedulerInit() { ChronoScheduler::instance().init(); }
