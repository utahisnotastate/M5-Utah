package com.utahisnotastate.m5utah.mesh

import com.utahisnotastate.m5utah.transport.FastPathUsbBridge
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.launch
import org.json.JSONObject

/**
 * Asymmetric gossip mesh participant (m5-android-mesh).
 *
 * Intercepts Fluxwire registry gossip, maintains a local units mirror, runs
 * pre-flight audits, and routes validated binwire frames over USB Host.
 */
class AndroidMeshParticipant(
    private val usbBridge: FastPathUsbBridge,
    private val nodeId: String = "android_host_node",
    private val scope: CoroutineScope = CoroutineScope(SupervisorJob() + Dispatchers.IO),
) {
    val registryMirror = MeshRegistryMirror()
    private val meshNode = FluxwireMeshNode(nodeId = nodeId, scope = scope)

    var onAuditFailure: ((List<String>) -> Unit)? = null
    var onFastPathRouted: ((Int) -> Unit)? = null

    fun start() {
        meshNode.onRegistryGossip = { payload -> handleRegistryGossip(payload) }
        meshNode.onPeerDegraded = { /* host may relay remediation */ }
        meshNode.start()
    }

    fun stop() {
        meshNode.stop()
    }

    fun publishLocalRegistry(registry: JSONObject) {
        registryMirror.applyRegistryGossip(registry)
        meshNode.updateRegistryFingerprint(registryMirror.fingerprint())
        meshNode.broadcastRegistryGossip(registry)
    }

    private fun handleRegistryGossip(payload: JSONObject) {
        val registry = payload.optJSONObject("registry") ?: return
        registryMirror.applyRegistryGossip(registry)
        meshNode.updateRegistryFingerprint(registryMirror.fingerprint())

        val auditErrors = MeshPreflightAudit.validateRegistry(registry)
        if (auditErrors.isNotEmpty()) {
            onAuditFailure?.invoke(auditErrors)
            return
        }

        val frame = MeshPreflightAudit.compileFirstBinwireFrame(registry)
        if (frame != null) {
            usbBridge.dispatchRawFrame(frame)
            onFastPathRouted?.invoke(frame.size)
        }
    }
}

object MeshPreflightAudit {
    private const val MAX_FREQUENCY_HZ = 60_000
    private const val MAX_UNITS = 10

    fun validateRegistry(registry: JSONObject): List<String> {
        val errors = mutableListOf<String>()
        val units = registry.optJSONObject("units") ?: registry
        if (units.length() > MAX_UNITS) {
            errors.add("registry exceeds max units ($MAX_UNITS)")
        }
        val keys = units.keys()
        while (keys.hasNext()) {
            val id = keys.next()
            val unit = units.optJSONObject(id) ?: continue
            val freq = unit.optInt("frequency_hz", -1)
            if (freq >= 0 && freq > MAX_FREQUENCY_HZ) {
                errors.add("unit $id frequency_hz exceeds safe limit")
            }
        }
        return errors
    }

    fun compileFirstBinwireFrame(registry: JSONObject): ByteArray? {
        val units = registry.optJSONObject("units") ?: registry
        val keys = units.keys()
        if (!keys.hasNext()) return null
        val unit = units.getJSONObject(keys.next())
        val binwire = unit.optJSONObject("binwire") ?: return null
        return com.utahisnotastate.m5utah.transport.BinwireFrame.pack(
            (binwire.optInt("unit_id", unit.optInt("unit_id", 0)) and 0xFF).toByte(),
            (binwire.optInt("pin", 0) and 0xFF).toByte(),
            binwire.optInt("frequency_hz", binwire.optInt("frequency", 0)).toShort(),
            binwire.optInt("state_flag", binwire.optInt("state_mask", 1)),
        )
    }
}
