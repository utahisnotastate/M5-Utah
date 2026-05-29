#pragma once

#include <ArduinoJson.h>

class CryptoEnclave {
 public:
  static bool verifyIntentSignature(const char *payload, const char *signatureHex);
  static bool verifyIntentObject(JsonObjectConst root);
  static bool requireSignedRegistry();

 private:
  static bool computeSha256Hex(const char *input, char *outHex, size_t outHexLen);
  static bool buildCanonicalBody(JsonObjectConst root, String &out);
};

void emitSecurityAlarm(const char *reason);
