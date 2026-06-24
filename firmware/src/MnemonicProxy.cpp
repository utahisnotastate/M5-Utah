#include "MnemonicProxy.h"

#include "MeshStateMirror.h"
#include "TimeTravelJournal.h"

#include <Arduino.h>
#include <WiFi.h>
#include <cstring>
#include <esp_now.h>
#include <esp_wifi.h>

uint8_t MnemonicProxy::ambient_nodes_[MnemonicProxy::kMaxAmbientNodes][6]{};
int MnemonicProxy::discovered_nodes_ = 0;
uint32_t MnemonicProxy::dispatch_count_ = 0;

namespace {

bool promiscuous_enabled = false;

void IRAM_ATTR promiscuousRx(void *buf, wifi_promiscuous_pkt_type_t type) {
  if (type != WIFI_PKT_MGMT && type != WIFI_PKT_DATA) {
    return;
  }
  const wifi_promiscuous_pkt_t *pkt = reinterpret_cast<wifi_promiscuous_pkt_t *>(buf);
  if (pkt == nullptr || pkt->rx_ctrl.sig_len < 12) {
    return;
  }
  MnemonicProxy::recordPromiscuousMac(pkt->payload + 10);
}

}  // namespace

void MnemonicProxy::init() {
  discovered_nodes_ = 0;
  dispatch_count_ = 0;
  memset(ambient_nodes_, 0, sizeof(ambient_nodes_));
  timeTravelRecord("mnemonic_proxy:init");
}

void MnemonicProxy::recordPromiscuousMac(const uint8_t *mac) {
  if (mac == nullptr || discovered_nodes_ >= kMaxAmbientNodes) {
    return;
  }
  for (int i = 0; i < discovered_nodes_; ++i) {
    if (memcmp(ambient_nodes_[i], mac, 6) == 0) {
      return;
    }
  }
  memcpy(ambient_nodes_[discovered_nodes_], mac, 6);
  discovered_nodes_++;
}

void MnemonicProxy::initiateHiveScan() {
  if (!MeshStateMirror::instance().isActive()) {
    return;
  }
  if (!promiscuous_enabled) {
    esp_wifi_set_promiscuous(true);
    esp_wifi_set_promiscuous_rx_cb(promiscuousRx);
    promiscuous_enabled = true;
  }
  delay(50);
  esp_wifi_set_promiscuous(false);
  promiscuous_enabled = false;
  timeTravelRecord("mnemonic_proxy:hive_scan");
}

bool MnemonicProxy::dispatchComputeTask(const float *matrix, size_t size) {
  if (matrix == nullptr || size == 0) {
    return false;
  }
  if (discovered_nodes_ == 0 || !MeshStateMirror::instance().isActive()) {
    return false;
  }

  ParasiticPayload payload{};
  payload.magic = kMagic;
  payload.task_id = static_cast<uint8_t>(esp_random() & 0xFF);
  const size_t chunk = size < 8 ? size : 8;
  memcpy(payload.tensor_chunk, matrix, chunk * sizeof(float));

  esp_now_peer_info_t peerInfo = {};
  memcpy(peerInfo.peer_addr, ambient_nodes_[0], 6);
  peerInfo.channel = 0;
  peerInfo.encrypt = false;
  esp_now_add_peer(&peerInfo);
  const esp_err_t result =
      esp_now_send(ambient_nodes_[0], reinterpret_cast<uint8_t *>(&payload), sizeof(payload));
  if (result == ESP_OK) {
    dispatch_count_++;
    return true;
  }
  return false;
}
