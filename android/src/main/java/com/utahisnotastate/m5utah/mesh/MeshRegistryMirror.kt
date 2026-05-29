package com.utahisnotastate.m5utah.mesh

import org.json.JSONObject
import java.security.MessageDigest

/**
 * In-memory mirror of registry/units.json state for Android mesh participants.
 */
class MeshRegistryMirror {
    private val units = linkedMapOf<String, JSONObject>()

    fun applyRegistryGossip(registry: JSONObject) {
        val block = registry.optJSONObject("units") ?: return
        val keys = block.keys()
        while (keys.hasNext()) {
            val unitId = keys.next()
            units[unitId] = block.getJSONObject(unitId)
        }
    }

    fun getUnit(unitId: String): JSONObject? = units[unitId]

    fun snapshot(): Map<String, JSONObject> = units.toMap()

    fun fingerprint(): String {
        val canonical = JSONObject()
        val unitsObj = JSONObject()
        units.forEach { (id, config) -> unitsObj.put(id, config) }
        canonical.put("units", unitsObj)
        val digest = MessageDigest.getInstance("SHA-256")
            .digest(canonical.toString().toByteArray(Charsets.UTF_8))
        return digest.take(8).joinToString("") { "%02x".format(it) }
    }
}
