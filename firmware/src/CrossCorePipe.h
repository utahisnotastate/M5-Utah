#pragma once

#include <Arduino.h>
#include <freertos/ringbuf.h>
#include <stddef.h>
#include <stdint.h>

constexpr size_t kCrossCoreRingBytes = 8192;
constexpr uint8_t kPipeFrameJson = 0x01;
constexpr uint8_t kPipeFrameBinary = 0x02;

class CrossCorePipe {
 public:
  void initializeBufferPipe();
  bool pushRawByteFrame(const uint8_t *byteBlock, size_t frameSize);
  void *receiveActiveFramePointer(size_t *retrievedSize);
  void releaseProcessedFrame(void *itemPointer);
  bool isReady() const;
  RingbufHandle_t nativeHandle() const { return intentRingBuffer_; }

 private:
  RingbufHandle_t intentRingBuffer_ = nullptr;
};

CrossCorePipe &globalCorePipe();

void startProtocolCoreIngestTask();
bool drainCorePipeFrames();
