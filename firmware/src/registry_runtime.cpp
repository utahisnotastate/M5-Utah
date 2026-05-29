#include "registry_runtime.h"

#include "DynamicMultiplexer.h"
#include "HandleMemory.h"
#include "BusArbitrator.h"
#include "PriorityGatekeeper.h"
#include "Sandbox.h"
#include "StateForker.h"
#include "TimeTravelJournal.h"

#include <cstring>

#include <M5Unified.h>

constexpr int kMaxUnits = 10;

static bool g_safeguard = false;

struct StableUnitSnapshot {
  char name[32];
  UnitTaskConfig cfg;
  bool valid;
};

static StableUnitSnapshot g_stableUnits[kMaxUnits];

static int findStableIndex(const char *unitName) {
  for (int i = 0; i < kMaxUnits; ++i) {
    if (g_stableUnits[i].valid && strcmp(g_stableUnits[i].name, unitName) == 0) {
      return i;
    }
  }
  return -1;
}

static int allocStableIndex() {
  for (int i = 0; i < kMaxUnits; ++i) {
    if (!g_stableUnits[i].valid) {
      return i;
    }
  }
  return -1;
}

static void registerBusArbitrationSlot(const char *unitId, JsonObjectConst unit, int frequencyHz) {
  const char *protocolType = unit["type"] | unit["bus_type"] | "";
  if (!isSharedBusProtocol(protocolType)) {
    return;
  }
  const int busUnitId = deriveBusUnitId(unitId);
  const uint32_t windowMs = defaultBusWindowMs(unit, frequencyHz);
  globalBusArbitrator().registerUnitSlot(busUnitId, windowMs);
}

static bool parseUnitConfig(const char *unitId, JsonObjectConst unit, UnitTaskConfig *cfg) {
  memset(cfg, 0, sizeof(UnitTaskConfig));
  strncpy(cfg->name, unitId, sizeof(cfg->name) - 1);
  const char *semantic = unit["semantic_action"] | "ACTION_INDICATE_STATUS_SUCCESS";
  strncpy(cfg->semantic, semantic, sizeof(cfg->semantic) - 1);
  cfg->frequencyHz = unit["frequency_hz"] | 2;
  if (cfg->frequencyHz < 1) cfg->frequencyHz = 1;
  if (cfg->frequencyHz > 60) cfg->frequencyHz = 60;
  cfg->priority = unit["priority"] | 1;
  cfg->assignedPriorityTier = priorityTierFromUnit(unit);
  cfg->priority = static_cast<int>(
      globalGatekeeper().tierToPriority(cfg->assignedPriorityTier));
  if (unit["priority"].is<int>()) {
    const int explicitPriority = unit["priority"].as<int>();
    if (explicitPriority > cfg->priority) {
      cfg->priority = explicitPriority;
    }
  }
  cfg->active = unit["state"] | true;
  cfg->sequenceId = unit["refresh_sequence_id"] | 0U;
  cfg->allocationHandleId = -1;
  cfg->bufferSizeBytes = 0;

  const size_t bufferSize = unit["buffer_size_bytes"] | 0;
  if (bufferSize > 0) {
    const size_t cappedSize = bufferSize > 512 ? 512 : bufferSize;
    const int preferredHandle = unit["allocation_handle_id"] | -1;
    const int handleId = preferredHandle >= 0
                             ? globalMemoryManager().bindHandle(preferredHandle, cappedSize)
                             : globalMemoryManager().allocateHandle(cappedSize);
    if (handleId >= 0) {
      cfg->allocationHandleId = handleId;
      cfg->bufferSizeBytes = static_cast<int>(cappedSize);
      globalMemoryManager().setHandleLocked(handleId, true);
      if (globalMemoryManager().resolveHandle(handleId) != nullptr) {
        Serial.printf("[MEMORY] Unit %s bound to virtual handle %d (%u bytes)\n", unitId, handleId,
                      static_cast<unsigned>(cappedSize));
      }
    }
  }
  return true;
}

static void forkUnitWithSnapshot(UnitTaskConfig *cfg, uint32_t seq) {
  if (StateForker::instance().stageAndForkUnit(cfg->name, cfg, seq, sandboxedUnitWorker)) {
    registryCaptureStableSnapshot(cfg->name, cfg);
    return;
  }
  Serial.printf("[STAGING] Fork rejected for %s — reverting to stable snapshot\n", cfg->name);
  registryRevertUnitToStable(cfg->name);
}

static void applyUnitsObject(JsonObjectConst units) {
  const char *keepIds[kMaxUnits];
  int keepCount = 0;

  for (JsonPairConst kv : units) {
    if (keepCount < kMaxUnits) {
      keepIds[keepCount++] = kv.key().c_str();
    }
  }

  StateForker::instance().terminateUnitsNotInList(keepIds, keepCount);

  for (JsonPairConst kv : units) {
    UnitTaskConfig cfg;
    parseUnitConfig(kv.key().c_str(), kv.value().as<JsonObjectConst>(), &cfg);
    registerBusArbitrationSlot(kv.key().c_str(), kv.value().as<JsonObjectConst>(), cfg.frequencyHz);
    DynamicMultiplexer::configureProcessorTopology(
        kv.value().as<JsonObjectConst>(), deriveBusUnitId(kv.key().c_str()),
        static_cast<UBaseType_t>(cfg.priority));
    uint32_t seq = cfg.sequenceId != 0 ? cfg.sequenceId : millis();
    forkUnitWithSnapshot(&cfg, seq);
  }
}

static void applyUnitsArray(JsonArrayConst unitsArr) {
  const char *keepIds[kMaxUnits];
  int keepCount = 0;

  for (JsonObjectConst unit : unitsArr) {
    const char *unitId = unit["unit_id"] | "unit";
    if (keepCount < kMaxUnits) {
      keepIds[keepCount++] = unitId;
    }
  }

  StateForker::instance().terminateUnitsNotInList(keepIds, keepCount);

  for (JsonObjectConst unit : unitsArr) {
    const char *unitId = unit["unit_id"] | "unit";
    UnitTaskConfig cfg;
    parseUnitConfig(unitId, unit, &cfg);
    registerBusArbitrationSlot(unitId, unit, cfg.frequencyHz);
    DynamicMultiplexer::configureProcessorTopology(unit, deriveBusUnitId(unitId),
                                                   static_cast<UBaseType_t>(cfg.priority));
    uint32_t seq = cfg.sequenceId != 0 ? cfg.sequenceId : millis();
    forkUnitWithSnapshot(&cfg, seq);
  }
}

void registryCaptureStableSnapshot(const char *unitName, const UnitTaskConfig *cfg) {
  int idx = findStableIndex(unitName);
  if (idx < 0) {
    idx = allocStableIndex();
  }
  if (idx < 0) {
    return;
  }
  strncpy(g_stableUnits[idx].name, unitName, sizeof(g_stableUnits[idx].name) - 1);
  memcpy(&g_stableUnits[idx].cfg, cfg, sizeof(UnitTaskConfig));
  g_stableUnits[idx].valid = true;
}

void registryRevertUnitToStable(const char *unitName) {
  int idx = findStableIndex(unitName);
  if (idx < 0) {
    return;
  }
  UnitTaskConfig restored = g_stableUnits[idx].cfg;
  uint32_t seq = restored.sequenceId != 0 ? restored.sequenceId : millis();
  Serial.printf("[SANDBOX] Reverting unit %s to last stable snapshot (seq %u)\n", unitName, seq);
  StateForker::instance().stageAndForkUnit(unitName, &restored, seq, sandboxedUnitWorker);
}

void registryRuntimeInit() {
  globalMemoryManager().initializeMemoryPool();
  globalBusArbitrator().initializeArbitrator();
  globalGatekeeper().initializeGatekeeper();
  StaticJsonDocument<256> doc;
  JsonObject unit = doc.to<JsonObject>();
  unit["frequency_hz"] = 2;
  unit["semantic_action"] = "ACTION_INDICATE_STATUS_SUCCESS";
  unit["priority"] = 1;
  unit["refresh_sequence_id"] = 1;

  StateForker::instance().resetAll();
  UnitTaskConfig cfg;
  parseUnitConfig("heartbeat", unit, &cfg);
  forkUnitWithSnapshot(&cfg, 1);
}

void registryHotReload(const JsonObjectConst &registryRoot) {
  g_safeguard = registryRoot["safeguard"] | false;
  timeTravelRecord("registry_hot_reload");

  if (g_safeguard) {
    DynamicMultiplexer::resetAll();
    StateForker::instance().resetAll();
  }

  JsonObjectConst units = registryRoot["units"].as<JsonObjectConst>();
  if (!units.isNull()) {
    applyUnitsObject(units);
    return;
  }

  JsonArrayConst unitsArr = registryRoot["units"].as<JsonArrayConst>();
  if (!unitsArr.isNull()) {
    applyUnitsArray(unitsArr);
  }
}

void registrySupervisorTick() {
  if (ESP.getFreeHeap() < 20000) {
    g_safeguard = true;
  }
  globalMemoryManager().compactIfPressure(0.92f);
}

void registryApplyBinwireUnit(const char *unitName, uint8_t pin, uint16_t frequencyHz,
                              uint32_t sequenceId) {
  UnitTaskConfig cfg;
  memset(&cfg, 0, sizeof(cfg));
  strncpy(cfg.name, unitName, sizeof(cfg.name) - 1);
  strncpy(cfg.semantic, "ACTION_INDICATE_STATUS_SUCCESS", sizeof(cfg.semantic) - 1);
  cfg.frequencyHz = frequencyHz > 0 ? frequencyHz : 2;
  if (cfg.frequencyHz > 60) cfg.frequencyHz = 60;
  cfg.priority = 2;
  cfg.active = true;
  cfg.sequenceId = sequenceId;

  StaticJsonDocument<128> doc;
  JsonObject unit = doc.to<JsonObject>();
  unit["type"] = "raw_gpio";
  JsonArray pins = unit["pins"].to<JsonArray>();
  pins.add(pin);
  unit["frequency_hz"] = cfg.frequencyHz;
  unit["refresh_sequence_id"] = sequenceId;
  DynamicMultiplexer::configureProcessorTopology(static_cast<JsonObjectConst>(unit),
                                                 deriveBusUnitId(unitName),
                                                 static_cast<UBaseType_t>(cfg.priority));

  uint32_t seq = sequenceId != 0 ? sequenceId : millis();
  forkUnitWithSnapshot(&cfg, seq);
}

void registryRespondCapabilities(JsonObject out) {
  JsonArray caps = out["capabilities"].to<JsonArray>();
  caps.add("display");
  caps.add("speaker");
  caps.add("power");
  caps.add("registry_hot_reload");
  caps.add("semantic_actions");
  caps.add("dynamic_bus_multiplexing");
  caps.add("gossip_mesh_node");
  caps.add("time_travel_journal");
  caps.add("zero_downtime_state_fork");
  caps.add("virtual_event_piping");
  caps.add("virtual_event_stochastic_filtering");
  caps.add("binwire_fastpath");
  caps.add("sandbox_isolation");
  caps.add("raft_consensus_node");
  caps.add("crypto_enclave");
  caps.add("kalman_telemetry_filter");
  caps.add("runtime_jit_linker");
  caps.add("vectorwire_causal_sync");
  caps.add("resource_pruning");
  caps.add("speculative_staging");
  caps.add("dag_state_graph");
  caps.add("delta_bitmask_engine");
  caps.add("bitmapped_graph_relational_delta");
  caps.add("unified_state_sync_loop");
  caps.add("speculative_branch_flattening");
  caps.add("hot_swappable_vector_fence");
  caps.add("closed_loop_autofence");
  caps.add("zero_copy_cross_core_stream");
  caps.add("mesh_registry_synchronizer");
  caps.add("android_gossip_mesh_participant");
  caps.add("assembly_trampoline_hook");
  caps.add("memory_overlay_compiler");
  caps.add("cross_core_ring_pipe");
  caps.add("zero_copy_tokenizer");
  caps.add("virtual_handle_memory");
  caps.add("predictive_heap_compaction");
  caps.add("tdma_bus_arbitrator");
  caps.add("telemetry_hamming_ecc");
  caps.add("priority_inheritance_gatekeeper");
  caps.add("m5_central_kernel");
  caps.add("resource_aware_orchestrator");
  caps.add("dual_core_execution_harness");
  caps.add("telemetry_self_healing_loop");
  caps.add("asymmetric_rpp_piping");
  caps.add("android_usb_host_bridge");
  if (M5.Imu.isEnabled()) caps.add("accel");
}
