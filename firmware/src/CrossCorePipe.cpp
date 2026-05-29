#include "CrossCorePipe.h"

#include "BinwireDecoder.h"
#include "BufferStream.h"
#include "DeltaEngine.h"
#include "DualCoreHarness.h"
#include "JumpKernel.h"
#include "MemoryOverlayDecoder.h"
#include "RemediationDecoder.h"
#include "SecureWireFence.h"
#include "StreamIntentDecoder.h"
#include "VectorFence.h"
#include "RPPDecoder.h"

#include <cstring>
#include <freertos/FreeRTOS.h>
#include <freertos/task.h>

static constexpr size_t kMaxPipePayload = 4096;
static constexpr uint32_t kIngestTaskStack = 6144;
static constexpr UBaseType_t kIngestTaskPriority = 3;

extern bool processInboundJsonPayload(char *payload, size_t len);
extern bool processInboundBinaryPayload(const uint8_t *data, size_t len, bool &ok);
extern void sendTransportAck(bool ok, const char *error);

CrossCorePipe &globalCorePipe() {
  static CrossCorePipe pipe;
  return pipe;
}

void CrossCorePipe::initializeBufferPipe() {
  Serial.printf(
      "[HARNESS] Allocating dual-core lock-free ring (%u bytes, min %u)...\n",
      static_cast<unsigned>(kFastPathQueueBytes), static_cast<unsigned>(kFastPathQueueMinBytes));
  intentRingBuffer_ = xRingbufferCreate(kCrossCoreRingBytes, RINGBUF_TYPE_NOSPLIT);
  if (intentRingBuffer_ == nullptr) {
    Serial.println("[CRITICAL ERROR] Failed to initialize cross-core allocation structures!");
  }
}

bool CrossCorePipe::isReady() const { return intentRingBuffer_ != nullptr; }

bool CrossCorePipe::pushRawByteFrame(const uint8_t *byteBlock, size_t frameSize) {
  if (intentRingBuffer_ == nullptr || byteBlock == nullptr || frameSize == 0) {
    return false;
  }
  if (frameSize > kMaxPipePayload + 1) {
    return false;
  }
  const BaseType_t success =
      xRingbufferSend(intentRingBuffer_, reinterpret_cast<void *>(const_cast<uint8_t *>(byteBlock)),
                      frameSize, 0);
  return success == pdTRUE;
}

void *CrossCorePipe::receiveActiveFramePointer(size_t *retrievedSize) {
  if (intentRingBuffer_ == nullptr || retrievedSize == nullptr) {
    return nullptr;
  }
  return xRingbufferReceive(intentRingBuffer_, retrievedSize, 0);
}

void CrossCorePipe::releaseProcessedFrame(void *itemPointer) {
  if (intentRingBuffer_ != nullptr && itemPointer != nullptr) {
    vRingbufferReturnItem(intentRingBuffer_, itemPointer);
  }
}

namespace {

bool readExactStream(Stream &stream, uint8_t *buffer, size_t len) {
  size_t offset = 0;
  const uint32_t start = millis();
  while (offset < len) {
    if (stream.available() > 0) {
      const int ch = stream.read();
      if (ch < 0) return false;
      buffer[offset++] = static_cast<uint8_t>(ch);
      continue;
    }
    if (millis() - start > 50) return false;
    delay(1);
  }
  return true;
}

uint32_t readU32BeStream(Stream &stream) {
  uint8_t buf[4];
  if (!readExactStream(stream, buf, 4)) return 0;
  return (static_cast<uint32_t>(buf[0]) << 24) | (static_cast<uint32_t>(buf[1]) << 16) |
         (static_cast<uint32_t>(buf[2]) << 8) | static_cast<uint32_t>(buf[3]);
}

bool pushPipeFrame(uint8_t kind, const uint8_t *payload, size_t payloadLen) {
  if (payloadLen + 1 > kMaxPipePayload) return false;
  uint8_t frame[kMaxPipePayload + 1];
  frame[0] = kind;
  if (payloadLen > 0) {
    memcpy(frame + 1, payload, payloadLen);
  }
  return globalCorePipe().pushRawByteFrame(frame, payloadLen + 1);
}

bool ingestBinaryFrame(Stream &stream) {
  const int lead = stream.peek();
  if (lead == static_cast<int>(kDeltaMagic0)) {
    uint8_t scratch[kMaxPipePayload];
    size_t frameLen = 0;
    if (!readExactStream(stream, scratch, 2)) return false;
    frameLen = 2;
    uint8_t headerBytes[3];
    if (!readExactStream(stream, headerBytes, 3)) return false;
    scratch[frameLen++] = headerBytes[0];
    scratch[frameLen++] = headerBytes[1];
    scratch[frameLen++] = headerBytes[2];
    const uint16_t slotMask =
        static_cast<uint16_t>((static_cast<uint16_t>(headerBytes[1]) << 8) | headerBytes[2]);
    for (int bit = 0; bit < kMaxDeltaSlots; bit++) {
      if ((slotMask & (1U << bit)) == 0) continue;
      if (!readExactStream(stream, scratch + frameLen, 2)) return false;
      frameLen += 2;
    }
    return pushPipeFrame(kPipeFrameBinary, scratch, frameLen);
  }

  if (lead != 0x23 || stream.available() < 2) return false;

  const uint8_t b0 = static_cast<uint8_t>(stream.read());
  const uint8_t b1 = static_cast<uint8_t>(stream.read());

  if (b0 == kOverlayMagic0 && b1 == kOverlayMagic1) {
    const uint32_t targetAddress = readU32BeStream(stream);
    const uint32_t payloadLength = readU32BeStream(stream);
    if (payloadLength == 0 || payloadLength > kMaxOverlayPayload) return false;
    const size_t frameLen = 2 + 8 + payloadLength;
    if (frameLen > kMaxPipePayload) return false;
    uint8_t scratch[kMaxPipePayload];
    scratch[0] = b0;
    scratch[1] = b1;
    scratch[2] = static_cast<uint8_t>((targetAddress >> 24) & 0xFF);
    scratch[3] = static_cast<uint8_t>((targetAddress >> 16) & 0xFF);
    scratch[4] = static_cast<uint8_t>((targetAddress >> 8) & 0xFF);
    scratch[5] = static_cast<uint8_t>(targetAddress & 0xFF);
    scratch[6] = static_cast<uint8_t>((payloadLength >> 24) & 0xFF);
    scratch[7] = static_cast<uint8_t>((payloadLength >> 16) & 0xFF);
    scratch[8] = static_cast<uint8_t>((payloadLength >> 8) & 0xFF);
    scratch[9] = static_cast<uint8_t>(payloadLength & 0xFF);
    if (!readExactStream(stream, scratch + 10, payloadLength)) return false;
    return pushPipeFrame(kPipeFrameBinary, scratch, frameLen);
  }

  if (b0 == kVectorFenceMagic0 && b1 == kVectorFenceMagic1) {
    uint8_t headerBytes[kVectorPatchHeaderLen];
    if (!readExactStream(stream, headerBytes, kVectorPatchHeaderLen)) return false;
    const uint16_t payloadLength =
        static_cast<uint16_t>((static_cast<uint16_t>(headerBytes[1]) << 8) | headerBytes[2]);
    if (payloadLength == 0 || payloadLength > kMaxVectorPatchPayload) return false;
    const size_t frameLen = 2 + kVectorPatchHeaderLen + payloadLength;
    if (frameLen > kMaxPipePayload) return false;
    uint8_t scratch[kMaxPipePayload];
    scratch[0] = b0;
    scratch[1] = b1;
    memcpy(scratch + 2, headerBytes, kVectorPatchHeaderLen);
    if (!readExactStream(stream, scratch + 2 + kVectorPatchHeaderLen, payloadLength)) return false;
    return pushPipeFrame(kPipeFrameBinary, scratch, frameLen);
  }

  if (b0 == kRemediationMagic0 && b1 == kRemediationMagic1) {
    uint8_t scratch[kRemediationFrameLen];
    scratch[0] = b0;
    scratch[1] = b1;
    if (!readExactStream(stream, scratch + 2, kRemediationFrameLen - 2)) return false;
    return pushPipeFrame(kPipeFrameBinary, scratch, kRemediationFrameLen);
  }

  if (b0 == kSecureWireMagic0 && b1 == kSecureWireMagic1) {
    uint8_t scratch[kSecureWireFrameLen];
    scratch[0] = b0;
    scratch[1] = b1;
    if (!readExactStream(stream, scratch + 2, sizeof(SecureIntentPacket))) return false;
    SecureIntentPacket packet{};
    memcpy(&packet, scratch + 2, sizeof(SecureIntentPacket));
    if (!globalSecureWireFence().verifyInboundSequenceFence(packet)) {
      return true;
    }
    return pushPipeFrame(kPipeFrameBinary, scratch, kSecureWireFrameLen);
  }

  if (b0 == kStreamMagic0 && b1 == kStreamMagic1) {
    uint8_t scratch[kStreamFrameLen];
    scratch[0] = b0;
    scratch[1] = b1;
    if (!readExactStream(stream, scratch + 2, kStreamFrameLen - 2)) return false;
    return pushPipeFrame(kPipeFrameBinary, scratch, kStreamFrameLen);
  }

  if (b0 == kRppMagic0 && b1 == kRppMagic1) {
    uint8_t scratch[kRppFrameLen];
    scratch[0] = b0;
    scratch[1] = b1;
    if (!readExactStream(stream, scratch + 2, sizeof(RPPCommandPacket))) return false;
    return pushPipeFrame(kPipeFrameBinary, scratch, kRppFrameLen);
  }

  if (b0 == kBitmapDeltaMagic0 && b1 == kBitmapDeltaMagic1) {
    uint8_t scratch[kBitmapDeltaFrameLen];
    scratch[0] = b0;
    scratch[1] = b1;
    if (!readExactStream(stream, scratch + 2, kBitmapDeltaFrameLen - 2)) return false;
    return pushPipeFrame(kPipeFrameBinary, scratch, kBitmapDeltaFrameLen);
  }

  if (b0 == kJumpFlattenMagic0 && b1 == kJumpFlattenMagic1) {
    uint8_t scratch[kJumpFlattenFrameLen];
    scratch[0] = b0;
    scratch[1] = b1;
    if (!readExactStream(stream, scratch + 2, kJumpFlattenFrameLen - 2)) return false;
    return pushPipeFrame(kPipeFrameBinary, scratch, kJumpFlattenFrameLen);
  }

  if (b0 == kBinwireMagic0 && b1 == kBinwireMagic1) {
    uint8_t scratch[kBinwireFrameLen];
    scratch[0] = b0;
    scratch[1] = b1;
    if (!readExactStream(stream, scratch + 2, sizeof(BinwireCommand))) return false;
    return pushPipeFrame(kPipeFrameBinary, scratch, kBinwireFrameLen);
  }

  return false;
}

void protocolCoreIngestTask(void *param) {
  (void)param;
  Serial.println("[CORE 0] Dual-core protocol ingestion kernel active (Feature 52).");
  static char lineBuffer[kMaxPipePayload + 1];

  for (;;) {
    if (Serial.available() <= 0) {
      vTaskDelay(pdMS_TO_TICKS(1));
      continue;
    }

    const int lead = Serial.peek();
    if (lead == static_cast<int>(kDeltaMagic0) ||
        (lead == 0x23 && Serial.available() >= 2)) {
      if (ingestBinaryFrame(Serial)) {
        continue;
      }
    }

    const int ch = Serial.read();
    if (ch < 0) continue;
    if (ch == '\n' || ch == '\r') continue;

    size_t length = 0;
    lineBuffer[length++] = static_cast<char>(ch);
    const uint32_t start = millis();
    while (length < kMaxPipePayload && millis() - start < 100) {
      if (Serial.available() > 0) {
        const int next = Serial.read();
        if (next < 0) break;
        if (next == '\n' || next == '\r') break;
        lineBuffer[length++] = static_cast<char>(next);
        continue;
      }
      vTaskDelay(pdMS_TO_TICKS(1));
    }
    lineBuffer[length] = '\0';
    pushPipeFrame(kPipeFrameJson, reinterpret_cast<uint8_t *>(lineBuffer), length);
  }
}

}  // namespace

void startProtocolCoreIngestTask() {
  xTaskCreatePinnedToCore(protocolCoreIngestTask, "ProtocolCore", kIngestTaskStack, nullptr,
                          kIngestTaskPriority, nullptr, 0);
}

extern bool m5KernelDrainPipeFrame();

bool drainCorePipeFrames() { return m5KernelDrainPipeFrame(); }
