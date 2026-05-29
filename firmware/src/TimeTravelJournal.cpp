#include "TimeTravelJournal.h"

#include <Arduino.h>
#include <ArduinoJson.h>
#include <cstring>

namespace {

constexpr int kStateHistoryMaxDepth = 8;
constexpr uint32_t kDumpHeapThreshold = 30000;
constexpr uint32_t kDumpCooldownMs = 5000;

struct StateSnapshot {
  uint32_t timestamp;
  uint32_t freeHeap;
  char intentActionHash[32];
};

class TimeTravelJournal {
 public:
  void recordStateTransition(const char *action, uint32_t currentHeap) {
    int index = headIndex_ % kStateHistoryMaxDepth;
    history_[index].timestamp = millis();
    history_[index].freeHeap = currentHeap;
    strncpy(history_[index].intentActionHash, action ? action : "unknown",
            sizeof(history_[index].intentActionHash) - 1);
    history_[index].intentActionHash[sizeof(history_[index].intentActionHash) - 1] = '\0';
    headIndex_++;
    if (snapshotCount_ < kStateHistoryMaxDepth) snapshotCount_++;
  }

  void maybeDump(uint32_t freeHeap) {
    if (freeHeap >= kDumpHeapThreshold) return;
    uint32_t now = millis();
    if (now - lastDumpMs_ < kDumpCooldownMs) return;
    lastDumpMs_ = now;
    dumpToFluxwire();
  }

  void dumpToFluxwire() {
    StaticJsonDocument<2048> doc;
    doc["type"] = "time_travel_journal_dump";
    doc["trigger_heap"] = ESP.getFreeHeap();
    doc["trigger_ms"] = millis();
    JsonArray records = doc["journal_records"].to<JsonArray>();

    for (int i = 0; i < snapshotCount_; i++) {
      int targetIndex = (headIndex_ - 1 - i + kStateHistoryMaxDepth) % kStateHistoryMaxDepth;
      JsonObject record = records.add<JsonObject>();
      record["relative_ms"] = millis() - history_[targetIndex].timestamp;
      record["allocated_heap_remaining"] = history_[targetIndex].freeHeap;
      record["intent_fingerprint"] = history_[targetIndex].intentActionHash;
    }

    Serial.print(F("[FLUXWIRE_TIME_TRAVEL_STREAM]:"));
    serializeJson(doc, Serial);
    Serial.println();
  }

 private:
  StateSnapshot history_[kStateHistoryMaxDepth];
  int headIndex_ = 0;
  int snapshotCount_ = 0;
  uint32_t lastDumpMs_ = 0;
};

TimeTravelJournal g_journal;

}  // namespace

void timeTravelRecord(const char *action) {
  g_journal.recordStateTransition(action, ESP.getFreeHeap());
}

void timeTravelMaybeDump(uint32_t freeHeap) {
  g_journal.maybeDump(freeHeap);
}

void timeTravelDump() {
  g_journal.dumpToFluxwire();
}
