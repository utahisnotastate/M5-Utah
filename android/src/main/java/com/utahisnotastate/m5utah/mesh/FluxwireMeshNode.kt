package com.utahisnotastate.m5utah.mesh

import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.launch
import org.json.JSONObject
import java.net.DatagramPacket
import java.net.DatagramSocket
import java.net.InetAddress

/**
 * Lightweight Fluxwire gossip mesh node for Android companion apps.
 * Mirrors host FluxwireGossipMesh (UDP port 23023).
 */
class FluxwireMeshNode(
    private val nodeId: String = "android_host_node",
    private val port: Int = 23023,
    private val scope: CoroutineScope = CoroutineScope(SupervisorJob() + Dispatchers.IO),
) {
    var onPeerDegraded: ((JSONObject) -> Unit)? = null
    var onRegistryGossip: ((JSONObject) -> Unit)? = null

    private var socket: DatagramSocket? = null
    private var localFingerprint: String = ""
    private var localStatus: String = "operational"

    fun start() {
        if (socket != null) return
        scope.launch {
            val sock = DatagramSocket(port)
            sock.broadcast = true
            socket = sock
            val buffer = ByteArray(2048)
            while (socket != null) {
                val packet = DatagramPacket(buffer, buffer.size)
                sock.receive(packet)
                val text = String(packet.data, 0, packet.length, Charsets.UTF_8)
                handleGossip(text)
            }
        }
        scope.launch {
            while (socket != null) {
                broadcastHeartbeat()
                kotlinx.coroutines.delay(5000)
            }
        }
    }

    fun stop() {
        socket?.close()
        socket = null
    }

    fun updateLocalStatus(status: String) {
        localStatus = status
    }

    fun updateRegistryFingerprint(fingerprint: String) {
        localFingerprint = fingerprint
    }

    fun broadcastRegistryGossip(registry: JSONObject) {
        scope.launch {
            val payload = JSONObject()
                .put("sender_id", nodeId)
                .put("type", "registry_gossip")
                .put("registry", registry)
                .put("fingerprint", localFingerprint)
                .put("status", localStatus)
            sendBroadcast(payload.toString())
        }
    }

    fun broadcastStatus() {
        scope.launch { broadcastHeartbeat() }
    }

    private fun broadcastHeartbeat() {
        val payload = JSONObject()
            .put("sender_id", nodeId)
            .put("type", "gossip_heartbeat")
            .put("fingerprint", localFingerprint)
            .put("status", localStatus)
        sendBroadcast(payload.toString())
    }

    private fun sendBroadcast(payload: String) {
        val sock = socket ?: return
        val bytes = payload.toByteArray(Charsets.UTF_8)
        val packet = DatagramPacket(
            bytes,
            bytes.size,
            InetAddress.getByName("255.255.255.255"),
            port,
        )
        sock.send(packet)
    }

    private fun handleGossip(text: String) {
        val json = runCatching { JSONObject(text) }.getOrNull() ?: return
        val sender = json.optString("sender_id", json.optString("node_id", ""))
        if (sender == nodeId) return

        json.optString("fingerprint").takeIf { it.isNotEmpty() }?.let { /* track peer fp */ }

        when (json.optString("type")) {
            "registry_gossip" -> onRegistryGossip?.invoke(json)
        }

        val status = json.optString("status")
        if (status == "degraded" || status == "degraded_state" || status == "error") {
            onPeerDegraded?.invoke(json)
        }
    }
}
