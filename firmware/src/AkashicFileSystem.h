#pragma once

#include <stddef.h>
#include <stdint.h>

/** Distributed RF-kinetic storage — fragments kept in continuous mesh flight (no SD/flash). */
class AkashicFileSystem {
public:
  static constexpr uint8_t kMagic = 0xAF;
  static constexpr size_t kPayloadBytes = 188;

  struct __attribute__((packed)) RfFragment {
    uint8_t magic;
    uint32_t file_id;
    uint16_t chunk_index;
    uint16_t chunk_total;
    uint8_t payload[kPayloadBytes];
    uint64_t decay_us;
  };

  static void init();
  static bool injectToVoid(uint32_t fileId, const uint8_t *data, size_t len);
  static void onFragmentCatch(const uint8_t *mac, const uint8_t *data, int len);
  static void maintainStandingWave();
  static uint32_t fragmentsInFlight() { return fragment_count_; }
  static uint32_t rebroadcastCount() { return rebroadcast_count_; }

private:
  static constexpr size_t kMaxFragments = 12;

  static RfFragment spatial_buffer_[kMaxFragments];
  static size_t fragment_count_;
  static uint32_t rebroadcast_count_;
};

inline void akashicFileSystemInit() { AkashicFileSystem::init(); }
