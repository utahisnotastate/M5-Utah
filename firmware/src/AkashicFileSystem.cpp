#include "AkashicFileSystem.h"

#include "MeshStateMirror.h"
#include "TimeTravelJournal.h"

#include <Arduino.h>
#include <cstring>
#include <esp_now.h>
#include <esp_timer.h>

AkashicFileSystem::RfFragment AkashicFileSystem::spatial_buffer_[AkashicFileSystem::kMaxFragments]{};
size_t AkashicFileSystem::fragment_count_ = 0;
uint32_t AkashicFileSystem::rebroadcast_count_ = 0;

namespace {

constexpr uint8_t kBroadcastMac[] = {0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF};
constexpr uint64_t kFlightMicros = 50000;

bool meshReady() { return MeshStateMirror::instance().isActive(); }

}  // namespace

void AkashicFileSystem::init() {
  fragment_count_ = 0;
  rebroadcast_count_ = 0;
  timeTravelRecord("akashic:init");
}

bool AkashicFileSystem::injectToVoid(uint32_t fileId, const uint8_t *data, size_t len) {
  if (data == nullptr || len == 0 || !meshReady()) {
    return false;
  }

  const uint16_t chunkTotal =
      static_cast<uint16_t>((len + kPayloadBytes - 1) / kPayloadBytes);
  for (uint16_t i = 0; i < chunkTotal; ++i) {
    RfFragment frag{};
    frag.magic = kMagic;
    frag.file_id = fileId;
    frag.chunk_index = i;
    frag.chunk_total = chunkTotal;
    const size_t offset = static_cast<size_t>(i) * kPayloadBytes;
    const size_t chunkLen = (len - offset) > kPayloadBytes ? kPayloadBytes : (len - offset);
    memcpy(frag.payload, data + offset, chunkLen);
    frag.decay_us = static_cast<uint64_t>(esp_timer_get_time()) + kFlightMicros;
    esp_now_send(kBroadcastMac, reinterpret_cast<uint8_t *>(&frag), sizeof(frag));
    rebroadcast_count_++;
  }
  timeTravelRecord("akashic:inject");
  return true;
}

void AkashicFileSystem::onFragmentCatch(const uint8_t *mac, const uint8_t *data, int len) {
  (void)mac;
  if (data == nullptr || len != static_cast<int>(sizeof(RfFragment))) {
    return;
  }
  const RfFragment *frag = reinterpret_cast<const RfFragment *>(data);
  if (frag->magic != kMagic) {
    return;
  }

  if (fragment_count_ < kMaxFragments) {
    spatial_buffer_[fragment_count_++] = *frag;
  } else {
    spatial_buffer_[fragment_count_ % kMaxFragments] = *frag;
  }
}

void AkashicFileSystem::maintainStandingWave() {
  if (!meshReady() || fragment_count_ == 0) {
    return;
  }

  const uint64_t now = static_cast<uint64_t>(esp_timer_get_time());
  size_t write = 0;
  for (size_t read = 0; read < fragment_count_; ++read) {
    RfFragment frag = spatial_buffer_[read];
    if (now > frag.decay_us) {
      frag.decay_us = now + kFlightMicros;
      esp_now_send(kBroadcastMac, reinterpret_cast<uint8_t *>(&frag), sizeof(frag));
      rebroadcast_count_++;
    } else {
      spatial_buffer_[write++] = frag;
    }
  }
  fragment_count_ = write;
}
