#include "InPlaceTokenizer.h"

InPlaceTokenView InPlaceTokenizer::tokenizeAndRoutePayload(char *rawInputBuffer,
                                                           size_t bufferLength) {
  InPlaceTokenView view;
  if (rawInputBuffer == nullptr || bufferLength == 0) {
    return view;
  }

  Serial.println(
      "[TOKENIZER] Executing zero-copy mutation pass across active IRAM memory registers...");

  char *scanPointer = rawInputBuffer;
  view.tokens[view.count++] = scanPointer;

  for (size_t i = 0; i < bufferLength && view.count < 8; i++) {
    const char ch = rawInputBuffer[i];
    if (ch == ',' || ch == ':') {
      rawInputBuffer[i] = '\0';
      if (i + 1 < bufferLength) {
        view.tokens[view.count++] = &rawInputBuffer[i + 1];
      }
    }
  }

  if (view.count >= 2) {
    Serial.printf(" -> Parsed Key Root Reference: %s\n", view.tokens[0]);
    Serial.printf(" -> Parsed Value Field Reference: %s\n", view.tokens[1]);
  }

  return view;
}
