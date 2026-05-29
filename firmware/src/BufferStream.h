#pragma once

#include <Arduino.h>
#include <stddef.h>
#include <stdint.h>

class BufferStream : public Stream {
 public:
  BufferStream(const uint8_t *data, size_t size) : data_(data), size_(size), pos_(0) {}

  int available() override { return static_cast<int>(size_ - pos_); }

  int read() override {
    if (pos_ >= size_) return -1;
    return static_cast<int>(data_[pos_++]);
  }

  int peek() override {
    if (pos_ >= size_) return -1;
    return static_cast<int>(data_[pos_]);
  }

  size_t write(uint8_t) override { return 0; }

  void reset() { pos_ = 0; }

 private:
  const uint8_t *data_;
  size_t size_;
  size_t pos_;
};
