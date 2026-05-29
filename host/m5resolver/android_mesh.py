"""Host-side contract mirror and preflight for Android mesh participants."""

from __future__ import annotations

from typing import Any

from .android_bridge import pack_android_binwire_frame
from .bus_validation import validate_bus_multiplexing

MAX_ANDROID_MESH_UNITS = 10
MAX_ANDROID_MESH_FREQUENCY_HZ = 60_000


def audit_android_mesh_registry(registry: dict[str, Any]) -> list[str]:
    """Mirror MeshPreflightAudit.validateRegistry on the Python host."""
    errors: list[str] = []
    units = registry.get("units", registry)
    if not isinstance(units, dict):
        return ["registry units must be an object"]
    if len(units) > MAX_ANDROID_MESH_UNITS:
        errors.append(f"registry exceeds max units ({MAX_ANDROID_MESH_UNITS})")
    for unit_id, config in units.items():
        if not isinstance(config, dict):
            continue
        freq = config.get("frequency_hz")
        if isinstance(freq, int) and freq > MAX_ANDROID_MESH_FREQUENCY_HZ:
            errors.append(f"unit {unit_id} frequency_hz exceeds safe limit")
    errors.extend(validate_bus_multiplexing({"units": units}))
    return errors


def compile_gossip_binwire_frame(registry: dict[str, Any]) -> bytes | None:
    """Extract first binwire hint from registry gossip and pack ## frame."""
    units = registry.get("units", registry)
    if not isinstance(units, dict) or not units:
        return None
    first_id = next(iter(units))
    unit = units[first_id]
    if not isinstance(unit, dict):
        return None
    binwire = unit.get("binwire")
    if isinstance(binwire, dict):
        return pack_android_binwire_frame(
            int(binwire.get("unit_id", unit.get("unit_id", 0))),
            int(binwire.get("pin", 0)),
            int(binwire.get("frequency_hz", binwire.get("frequency", 0))),
            int(binwire.get("state_flag", binwire.get("state_mask", 1))),
        )
    if "frequency_hz" in unit:
        return pack_android_binwire_frame(
            int(unit.get("unit_id", 0)),
            int(unit.get("pin", 0)),
            int(unit.get("frequency_hz", 0)),
            int(unit.get("state_mask", 1)),
        )
    return None
