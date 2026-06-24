#include "AcousticMask.h"

#include "StochasticShield.h"
#include "TimeTravelJournal.h"

#include <Arduino.h>
#include <esp_random.h>
#include <freertos/FreeRTOS.h>
#include <freertos/task.h>

#if __has_include(<driver/i2s.h>)
#include <driver/i2s.h>
#define SOVEREIGN_HAS_LEGACY_I2S 1
#endif

namespace {

constexpr int kSampleRate = 44100;
constexpr int kBufferSamples = 256;

#ifdef SOVEREIGN_HAS_LEGACY_I2S
constexpr i2s_port_t kI2sPort = I2S_NUM_0;
#endif

TaskHandle_t g_phononTask = nullptr;

void phononMaskTask(void *param) {
  (void)param;
  AcousticMask::executeSaturatedStream();
}

}  // namespace

bool AcousticMask::active_ = false;
uint32_t AcousticMask::frames_written_ = 0;

bool AcousticMask::initHardwareAudio() {
#ifdef SOVEREIGN_HAS_LEGACY_I2S
  i2s_config_t i2sConfig = {};
  i2sConfig.mode = static_cast<i2s_mode_t>(I2S_MODE_MASTER | I2S_MODE_TX);
  i2sConfig.sample_rate = kSampleRate;
  i2sConfig.bits_per_sample = I2S_BITS_PER_SAMPLE_16BIT;
  i2sConfig.channel_format = I2S_CHANNEL_FMT_ONLY_LEFT;
  i2sConfig.communication_format = I2S_COMM_FORMAT_STAND_I2S;
  i2sConfig.intr_alloc_flags = ESP_INTR_FLAG_LEVEL1;
  i2sConfig.dma_buf_count = 4;
  i2sConfig.dma_buf_len = kBufferSamples;
  i2sConfig.use_apll = false;
  i2sConfig.tx_desc_auto_clear = true;

  i2s_pin_config_t pinConfig = {};
  pinConfig.bck_io_num = 12;
  pinConfig.ws_io_num = 13;
  pinConfig.data_out_num = 14;
  pinConfig.data_in_num = I2S_PIN_NO_CHANGE;

  if (i2s_driver_install(kI2sPort, &i2sConfig, 0, nullptr) != ESP_OK) {
    Serial.println("[ACOUSTIC MASK] I2S unavailable — phonon routing disabled.");
    return false;
  }
  if (i2s_set_pin(kI2sPort, &pinConfig) != ESP_OK) {
    i2s_driver_uninstall(kI2sPort);
    Serial.println("[ACOUSTIC MASK] I2S pin config failed.");
    return false;
  }

  active_ = true;
  timeTravelRecord("acoustic_mask:i2s_online");
  Serial.println("[ACOUSTIC MASK] Phonon-routing DMA mask armed (Core 0 task).");
  return true;
#else
  Serial.println("[ACOUSTIC MASK] Legacy I2S driver not present — skipped.");
  return false;
#endif
}

void AcousticMask::executeSaturatedStream() {
#ifdef SOVEREIGN_HAS_LEGACY_I2S
  int16_t sampleBuffer[kBufferSamples];
  while (active_) {
    for (int i = 0; i < kBufferSamples; ++i) {
      const uint32_t entropy = StochasticShield::brownianEntropy();
      sampleBuffer[i] = static_cast<int16_t>((entropy & 0xFFFF) - 0x8000);
    }

    size_t bytesWritten = 0;
    if (i2s_write(kI2sPort, sampleBuffer, sizeof(sampleBuffer), &bytesWritten, portMAX_DELAY) ==
        ESP_OK) {
      frames_written_++;
    }

    delayMicroseconds(StochasticShield::jitterMicros());
    taskYIELD();
  }
#else
  vTaskDelete(nullptr);
#endif
}

void acousticMaskStartTask() {
  if (!AcousticMask::isActive() || g_phononTask != nullptr) {
    return;
  }
  xTaskCreatePinnedToCore(phononMaskTask, "mask_phonon", 4096, nullptr, 1, &g_phononTask, 0);
}
