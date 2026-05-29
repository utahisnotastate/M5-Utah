#pragma once

#include <Arduino.h>
#include <stddef.h>
#include <stdint.h>

struct InPlaceTokenView {
  const char *tokens[8];
  int count = 0;
};

class InPlaceTokenizer {
 public:
  static InPlaceTokenView tokenizeAndRoutePayload(char *rawInputBuffer, size_t bufferLength);
};
