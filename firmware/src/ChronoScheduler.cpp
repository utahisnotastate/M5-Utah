#include "ChronoScheduler.h"

#include "StochasticShield.h"
#include "TimeTravelJournal.h"

#include <Arduino.h>
#include <esp_timer.h>

namespace {

esp_timer_handle_t g_hyper_timer = nullptr;

void chronoSchedulerHyperTick(void *arg) {
  (void)arg;
  ChronoScheduler::instance().onHyperTick();
}

}  // namespace

ChronoScheduler &ChronoScheduler::instance() {
  static ChronoScheduler scheduler;
  return scheduler;
}

void ChronoScheduler::init() {
  if (g_hyper_timer != nullptr) {
    return;
  }

  esp_timer_create_args_t timer_args = {};
  timer_args.callback = &chronoSchedulerHyperTick;
  timer_args.name = "chrono_bypass";
  timer_args.dispatch_method = ESP_TIMER_TASK;

  if (esp_timer_create(&timer_args, &g_hyper_timer) != ESP_OK) {
    Serial.println("[CHRONO] Hyper-timer creation failed.");
    return;
  }

  if (esp_timer_start_periodic(g_hyper_timer, 100) != ESP_OK) {
    Serial.println("[CHRONO] Hyper-timer start failed.");
    return;
  }

  timeTravelRecord("chrono:init");
  Serial.println("[CHRONO] Predictive execution scheduler online (100us hyper-tick).");
}

void ChronoScheduler::injectFutureState(void (*task)(void), uint32_t expectedDeltaUs) {
  if (task == nullptr) {
    return;
  }
  FutureStateNode &slot = probability_matrix_[current_vector_];
  slot.speculative_task = task;
  slot.simulated_timestamp_us =
      static_cast<uint32_t>(esp_timer_get_time() + static_cast<uint64_t>(expectedDeltaUs));
  slot.is_committed = false;
  current_vector_ = static_cast<uint8_t>((current_vector_ + 1) % 3);
}

void ChronoScheduler::onHyperTick() {
  const uint64_t now = esp_timer_get_time();
  for (FutureStateNode &slot : probability_matrix_) {
    if (slot.is_committed || slot.speculative_task == nullptr) {
      continue;
    }
    if (now < slot.simulated_timestamp_us) {
      continue;
    }
    StochasticShield::executeWithBrownianJitter(slot.speculative_task);
    slot.is_committed = true;
    committed_count_++;
    timeTravelRecord("chrono:commit");
  }
}
