#include <Arduino.h>
#include <M5Unified.h>
#include <ArduinoJson.h>

#include "registry_runtime.h"
#include "TimeTravelJournal.h"
#include "BinwireDecoder.h"
#include "MemoryOverlayDecoder.h"
#include "RPPDecoder.h"
#include "AssemblyHook.h"
#include "DeltaEngine.h"
#include "JumpKernel.h"
#include "RemediationDecoder.h"
#include "SecureWireFence.h"
#include "StreamIntentDecoder.h"
#include "TransactionalCoreManager.h"
#include "VectorFence.h"
#include "SystemHealthHarvester.h"
#include "Sandbox.h"
#include "CryptoEnclave.h"
#include "TelemetryFilter.h"
#include "RuntimeLinker.h"
#include "M5Jit.h"
#include "SpeculativeStaging.h"
#include "VectorTelemetry.h"
#include "CrossCorePipe.h"
#include "InPlaceTokenizer.h"
#include "BufferStream.h"
#include "HandleMemory.h"
#include "BusArbitrator.h"
#include "TelemetryEcc.h"
#include "PriorityGatekeeper.h"
#include "M5Kernel.h"
#include "ResourceOrchestrator.h"
#include "DualCoreHarness.h"
#include "M5IntegratedKernel.h"
#include "TelemetryHealth.h"

static constexpr uint32_t BAUDRATE = 115200;
static constexpr size_t MAX_PAYLOAD = 4096;

// m5-kernel integrated runtime (see M5IntegratedKernel.h):
// Core 0 CrossCorePipe → lock-free ring → Core 1 M5Kernel + PriorityGatekeeper + BusArbitrator.
// Do NOT replace with ad-hoc xRingbufferCreate tasks — use M5Kernel::start().

static TelemetryFilterBank g_telemetryFilters;

void sendAck(bool ok, const char *error = "") {
  StaticJsonDocument<512> doc;
  doc["type"] = "ack";
  doc["ok"] = ok;
  if (!ok) {
    doc["error"] = error;
    timeTravelRecord("ack:error");
    timeTravelDump();
  }
  serializeJson(doc, Serial);
  Serial.println();
}

void recordIntentSummary(JsonObjectConst root) {
  if (root.containsKey("registry")) {
    timeTravelRecord("intent:registry");
    return;
  }
  if (root["capability_query"] | false) {
    timeTravelRecord("intent:capability_query");
    return;
  }
  if (root.containsKey("display")) timeTravelRecord("intent:display");
  else if (root.containsKey("speaker")) timeTravelRecord("intent:speaker");
  else if (root.containsKey("power")) timeTravelRecord("intent:power");
  else if (root.containsKey("native_jit")) timeTravelRecord("intent:native_jit");
  else timeTravelRecord("intent:unknown");
}

bool resolveNativeJitObject(JsonObjectConst jit) {
  const char *payloadHex = jit["payload_hex"] | "";
  size_t declaredSize = jit["code_size_bytes"] | 0;
  bool execute = jit["execute"] | true;

  if (jit.containsKey("type")) {
    const char *jitType = jit["type"] | "";
    if (strcmp(jitType, "native_jit_patch") != 0) {
      return false;
    }
  }

  return resolveNativeJitIntent(payloadHex, declaredSize, execute);
}

bool resolveNativeJitUnits(JsonObjectConst units) {
  for (JsonPairConst kv : units) {
    JsonObjectConst unit = kv.value().as<JsonObjectConst>();
    const char *unitType = unit["type"] | "";
    if (strcmp(unitType, "native_jit_patch") != 0) {
      continue;
    }
    if (resolveNativeJitObject(unit)) {
      return true;
    }
  }
  return false;
}

void resolveDisplayIntent(const JsonObjectConst &display) {
  if (display["clear"] | false) {
    uint16_t bg = display["bg_color"] | 0x0000;
    M5.Display.fillScreen(bg);
  }

  if (display.containsKey("text")) {
    JsonObjectConst text = display["text"].as<JsonObjectConst>();
    const int x = text["x"] | 0;
    const int y = text["y"] | 0;
    const int size = text["size"] | 2;
    const uint16_t color = text["color"] | 0xFFFF;
    const char *payload = text["payload"] | "";

    M5.Display.setTextSize(size);
    M5.Display.setTextColor(color);
    M5.Display.drawString(payload, x, y);
  }
}

void resolveSpeakerIntent(const JsonObjectConst &speaker) {
  if (speaker.containsKey("tone")) {
    JsonObjectConst tone = speaker["tone"].as<JsonObjectConst>();
    const double frequency = tone["frequency"] | 440.0;
    const int duration = tone["duration"] | 50;
    const int channel = tone["channel"] | 0;
    M5.Speaker.tone(frequency, duration, channel);
    return;
  }

  if (speaker["stop"] | false) {
    M5.Speaker.stop();
  }
}

void resolvePowerIntent(const JsonObjectConst &power) {
  if (power.containsKey("led")) {
    uint8_t brightness = power["led"] | 0;
    M5.Power.setLed(brightness);
  }

  if (power["off"] | false) {
    M5.Power.powerOff();
  }
}

void emitTelemetry() {
  telemetryHealthUpdateOrchestrationJitter();
  uint32_t freeHeap = ESP.getFreeHeap();
  timeTravelMaybeDump(freeHeap);

  StaticJsonDocument<768> doc;
  doc["type"] = "telemetry";
  if (freeHeap < 20000) {
    doc["status"] = "error";
  } else if (freeHeap < 30000) {
    doc["status"] = "degraded";
  } else {
    doc["status"] = "operational";
  }
  doc["board_id"] = static_cast<int>(M5.getBoard());
  doc["ts_us"] = micros();
  doc["unit_id"] = static_cast<int>(telemetryHealthActiveUnit());
  doc["active_pin"] = static_cast<int>(telemetryHealthActivePin());
  doc["battery_pct"] = M5.Power.getBatteryLevel();
  doc["charging"] = static_cast<int>(M5.Power.isCharging());

  JsonObject metrics = doc["metrics"].to<JsonObject>();
  metrics["free_heap"] = freeHeap;
  metrics["latency_budget_ms"] = 50;
  metrics["i2c_bandwidth_pct"] = 35;
  metrics["handle_pool_top"] = static_cast<int>(globalMemoryManager().poolTop());
  metrics["handle_pool_limit"] = static_cast<int>(globalMemoryManager().poolLimit());
  metrics["handle_fragmentation_index"] = globalMemoryManager().fragmentationIndex();
  metrics["handle_active_count"] = globalMemoryManager().activeHandleCount();
  metrics["bus_arbitrated_slots"] = globalBusArbitrator().activeSlotCount();
  metrics["bus_rejected_transactions"] = static_cast<int>(globalBusArbitrator().rejectedTransactions());
  metrics["gatekeeper_boost_count"] = static_cast<int>(globalGatekeeper().proactiveBoostCount());
  metrics["gatekeeper_lock_count"] = globalGatekeeper().activeLockCount();
  metrics["kernel_processed_frames"] = static_cast<int>(M5Kernel::processedFrameCount());
  metrics["kernel_orchestration_ticks"] = static_cast<int>(M5Kernel::orchestrationTicks());
  metrics["orchestrator_pressure_level"] =
      static_cast<int>(globalResourceOrchestrator().lastPressureLevel());
  metrics["orchestrator_deferred_frames"] =
      static_cast<int>(globalResourceOrchestrator().deferredFrameCount());
  metrics["orchestrator_staged_contexts"] =
      static_cast<int>(globalResourceOrchestrator().stagedContextCount());
  metrics["task_jitter_ms"] = static_cast<int>(telemetryHealthLastLoopJitterMs());
  metrics["active_unit_id"] = static_cast<int>(telemetryHealthActiveUnit());
  metrics["active_pin"] = static_cast<int>(telemetryHealthActivePin());

  const char *statusStr = doc["status"].as<const char *>();
  const uint8_t batteryPct = static_cast<uint8_t>(M5.Power.getBatteryLevel());
  JsonObject ecc = doc["ecc"].to<JsonObject>();
  ecc["status_word"] = TelemetryEcc::encodeNibble(telemetryStatusCode(statusStr));
  ecc["battery_word"] = TelemetryEcc::encodeNibble(static_cast<uint8_t>((batteryPct / 7) & 0x0F));
  ecc["heap_word"] =
      TelemetryEcc::encodeNibble(static_cast<uint8_t>((freeHeap >> 12) & 0x0F));

  if (M5.Imu.isEnabled()) {
    M5.Imu.update();
    auto data = M5.Imu.getImuData();
    float fx = 0.0f;
    float fy = 0.0f;
    float fz = 0.0f;
    g_telemetryFilters.filterImu(data.accel.x, data.accel.y, data.accel.z, fx, fy, fz);

    JsonObject accel = doc["accel"].to<JsonObject>();
    accel["x"] = fx;
    accel["y"] = fy;
    accel["z"] = fz;
    JsonObject accelRaw = doc["accel_raw"].to<JsonObject>();
    accelRaw["x"] = data.accel.x;
    accelRaw["y"] = data.accel.y;
    accelRaw["z"] = data.accel.z;
  }

  vectorTelemetry().attachToTelemetry(doc.as<JsonObject>(), 0);

  serializeJson(doc, Serial);
  Serial.println();

  if (freeHeap < 30000 || telemetryHealthLastLoopJitterMs() > 50) {
    Serial.print("[TELEMETRY_STREAM]:");
    serializeJson(doc, Serial);
    Serial.println();
  }
}

void emitHardwareEvent(const char *eventType, JsonObjectConst metadata) {
  StaticJsonDocument<512> doc;
  doc["type"] = "hardware_event";
  doc["event_type"] = eventType;
  JsonObject payload = doc["payload"].to<JsonObject>();
  for (JsonPairConst kv : metadata) {
    payload[kv.key()] = kv.value();
  }
  vectorTelemetry().attachToEvent(doc.as<JsonObject>());
  serializeJson(doc, Serial);
  Serial.println();
}

void sendTransportAck(bool ok, const char *error) { sendAck(ok, error); }

int dispatchBinaryTransportStream(Stream &stream, bool &ok) {
  if (stream.available() < 2) {
    return 0;
  }

  const int lead = stream.peek();
  if (lead == static_cast<int>(kDeltaMagic0)) {
    ok = DeltaEngine::tryProcess(stream);
    return ok ? 1 : -1;
  }

  if (lead != 0x23) {
    return 0;
  }

  const uint8_t b0 = static_cast<uint8_t>(stream.read());
  const uint8_t b1 = static_cast<uint8_t>(stream.read());

  if (b0 == kOverlayMagic0 && b1 == kOverlayMagic1) {
    const OverlayProcessResult result = MemoryOverlayDecoder::processPayload(stream);
    if (result == OverlayProcessResult::Applied) {
      ok = true;
      return 1;
    }
    ok = false;
    return -1;
  }

  if (b0 == kVectorFenceMagic0 && b1 == kVectorFenceMagic1) {
    ok = VectorFenceEngine::processPayload(stream);
    return ok ? 1 : -1;
  }

  if (b0 == kRemediationMagic0 && b1 == kRemediationMagic1) {
    ok = RemediationDecoder::processPayload(stream);
    return ok ? 1 : -1;
  }

  if (b0 == kSecureWireMagic0 && b1 == kSecureWireMagic1) {
    ok = SecureWireDecoder_processPayload(stream);
    return ok ? 1 : -1;
  }

  if (b0 == kStreamMagic0 && b1 == kStreamMagic1) {
    ok = StreamIntentDecoder::processPayload(stream);
    return ok ? 1 : -1;
  }

  if (b0 == kRppMagic0 && b1 == kRppMagic1) {
    ok = MicroExecutionKernel::processPayload(stream);
    return ok ? 1 : -1;
  }

  if (b0 == kBitmapDeltaMagic0 && b1 == kBitmapDeltaMagic1) {
    ok = DeltaEngine::processBitmapDeltaPayload(stream);
    return ok ? 1 : -1;
  }

  if (b0 == kJumpFlattenMagic0 && b1 == kJumpFlattenMagic1) {
    ok = MicroJumpKernel::processPayload(stream);
    return ok ? 1 : -1;
  }

  if (b0 == kBinwireMagic0 && b1 == kBinwireMagic1) {
    ok = BinwireDecoder::processPayload(stream);
    return ok ? 1 : -1;
  }

  ok = false;
  return -1;
}

bool processInboundBinaryPayload(const uint8_t *data, size_t len, bool &ok) {
  if (data == nullptr || len < 2) {
    ok = false;
    return true;
  }
  BufferStream stream(data, len);
  const int result = dispatchBinaryTransportStream(stream, ok);
  return result != 0;
}

bool processInboundJsonPayload(char *payload, size_t len) {
  if (payload == nullptr || len == 0 || len > MAX_PAYLOAD) {
    sendAck(false, len > MAX_PAYLOAD ? "payload_too_large" : "empty_payload");
    return true;
  }

  if (payload[0] != '{' && payload[0] != '[') {
    InPlaceTokenizer::tokenizeAndRoutePayload(payload, len);
    sendAck(true);
    return true;
  }

  StaticJsonDocument<MAX_PAYLOAD> doc;
  const auto err = deserializeJson(doc, payload);
  if (err) {
    sendAck(false, err.c_str());
    return true;
  }

  JsonObjectConst root = doc.as<JsonObjectConst>();

  if (!CryptoEnclave::verifyIntentObject(root)) {
    emitSecurityAlarm("intent_signature_verification_failed");
    sendAck(false, "security_signature_rejected");
    return true;
  }

  recordIntentSummary(root);

  if (root.containsKey("vector_clock_sync")) {
    vectorTelemetry().applyHostVectorSync(root["vector_clock_sync"].as<JsonObjectConst>());
  }

  if (root["capability_query"] | false) {
    StaticJsonDocument<256> capsDoc;
    JsonObject capsObj = capsDoc.to<JsonObject>();
    registryRespondCapabilities(capsObj);
    StaticJsonDocument<384> ackDoc;
    ackDoc["type"] = "ack";
    ackDoc["ok"] = true;
    ackDoc["capabilities"] = capsObj["capabilities"];
    serializeJson(ackDoc, Serial);
    Serial.println();
    return true;
  }

  if (root.containsKey("memory_compact")) {
    globalMemoryManager().compactMemoryPool();
    sendAck(true);
    return true;
  }

  if (root.containsKey("transaction_prepare")) {
    JsonObjectConst prep = root["transaction_prepare"].as<JsonObjectConst>();
    const uint16_t requested =
        static_cast<uint16_t>(prep["requested_buffer_bytes"] | 512);
    const bool approved = TransactionalCoreManager::evaluateTransactionFeasibility(requested);
    StaticJsonDocument<192> voteDoc;
    voteDoc["type"] = "transaction_vote";
    voteDoc["ok"] = approved;
    if (prep.containsKey("transaction_id")) {
      voteDoc["transaction_id"] = prep["transaction_id"];
    }
    serializeJson(voteDoc, Serial);
    Serial.println();
    return true;
  }

  if (root.containsKey("registry")) {
    JsonObjectConst reg = root["registry"].as<JsonObjectConst>();
    if (root["transaction_commit"] | false) {
      const size_t payloadEstimate = measureJson(reg);
      const uint16_t demand =
          TransactionalCoreManager::estimateRegistryBufferDemand(payloadEstimate);
      if (!TransactionalCoreManager::evaluateTransactionFeasibility(demand)) {
        sendAck(false, "transaction_commit_rejected");
        return true;
      }
    }
    registryHotReload(reg);
    sendAck(true);
    return true;
  }

  if (root.containsKey("native_jit")) {
    if (!resolveNativeJitObject(root["native_jit"].as<JsonObjectConst>())) {
      sendAck(false, "native_jit_injection_failed");
      return true;
    }
    sendAck(true);
    return true;
  }

  if (root.containsKey("units")) {
    JsonObjectConst units = root["units"].as<JsonObjectConst>();
    if (!units.isNull() && resolveNativeJitUnits(units)) {
      sendAck(true);
      return true;
    }
  }

  if (root.containsKey("display")) {
    resolveDisplayIntent(root["display"].as<JsonObjectConst>());
  }
  if (root.containsKey("speaker")) {
    resolveSpeakerIntent(root["speaker"].as<JsonObjectConst>());
  }
  if (root.containsKey("power")) {
    resolvePowerIntent(root["power"].as<JsonObjectConst>());
  }

  sendAck(true);
  return true;
}

void setup() {
  auto cfg = M5.config();
  cfg.serial_baudrate = BAUDRATE;
  cfg.clear_display = true;
  cfg.internal_imu = true;
  cfg.internal_rtc = true;
  cfg.internal_spk = true;
  M5.begin(cfg);

  M5.Display.setRotation(1);
  M5.Display.setTextSize(2);
  M5.Display.println("M5 Resolver Online");

  M5.Speaker.setVolume(64);
  M5.Speaker.tone(880, 60);

  timeTravelRecord("boot");
  m5IntegratedKernelBoot();
  vectorTelemetry().setNodeId("m5_node_01");
  Serial.println("[INTEGRATION INIT] m5-utah unified lifecycle entry point online.");
  Serial.println("[SANDBOX] Hardware isolation barriers armed for dynamic units.");
  Serial.println("[STAGING] Speculative shadow buffer armed for hot-reload promotion.");
  Serial.println("[DELTA] Bitmapped structural state engine online.");
  Serial.println("[FLATTEN] Speculative branch-flattening jump matrix online.");
  Serial.println("[VECTORFENCE] Hot-swappable IRAM interrupt vector matrix online.");
  Serial.println("[AUTOFENCE] Closed-loop telemetry remediation matrix online.");
  Serial.println("[STREAM] Zero-copy cross-core stream piping online.");
  Serial.println("[MESH SYNC] Transactional 2PC core manager online.");
  Serial.println("[ASSEMBLY] Virtual trampoline hook engine armed.");
  Serial.println("[IMMORTAL] Autonomic Grove I2C discovery online (flash once, vibe forever).");
  Serial.println("[M5-KERNEL] Integrated asymmetric dual-core runtime online.");
  Serial.println("[HARNESS] Dual-core execution harness online (512+ byte ring, Core 0/1 pinned).");
  Serial.println("[PIPE] Cross-core lock-free ring buffer online (Core 0 ingest / Core 1 exec).");
  Serial.println("[MEMORY] Virtual handle matrix and predictive compactor armed.");
  Serial.println("[ARBITRATOR] TDMA shared-bus containment matrix online.");
  Serial.println("[ECC] Hamming telemetry protection enabled.");
  Serial.println("[GATEKEEPER] Predictive priority-inheritance barriers armed.");
  Serial.println("[M5-KERNEL] Central processing registry core online.");
  Serial.println("[ORCHESTRATOR] Predictive resource arbitration staging armed.");
}

void loop() {
  vTaskDelay(portMAX_DELAY);
}
