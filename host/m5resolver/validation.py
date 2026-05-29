from __future__ import annotations

from typing import Any

from .bus_validation import validate_bus_multiplexing
from .dual_core_harness import validate_execution_core_unit
from .graph_engine import StateGraphEngine
from .jit_compiler import validate_jit_units, validate_native_jit_block
from .memory_profiler import HostMemoryProfiler
from .safety import validate_intent_safety
from .scheduler_compiler import HostSchedulerCompiler
from .security import require_signature_for_registry, verify_intent_signature


class IntentValidator:
    """Strict validator that raises on first error batch (for tests and gates)."""

    def __init__(self, *, require_registry_signature: bool = False) -> None:
        self.require_registry_signature = require_registry_signature

    def validate_intent_payload(self, intent: dict[str, Any]) -> None:
        errors = validate_intent_payload(
            intent, require_registry_signature=self.require_registry_signature
        )
        if errors:
            raise ValueError("; ".join(errors))

    def validate_registry(self, registry: dict[str, Any]) -> None:
        errors = validate_registry_payload(registry)
        if errors:
            raise ValueError("; ".join(errors))

    def validate_intent_security(self, intent: dict[str, Any]) -> list[str]:
        return verify_intent_signature(intent)

    def validate(self, intent: dict[str, Any]) -> bool:
        """Return True when intent passes full schema and safety invariants."""
        return not validate_intent_payload(
            intent, require_registry_signature=self.require_registry_signature
        )


def validate_registry_payload(registry: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    errors.extend(validate_intent_safety({"registry": registry}))
    errors.extend(validate_bus_multiplexing(registry))
    return errors


def validate_intent_payload(
    intent: dict[str, Any], *, require_registry_signature: bool = False
) -> list[str]:
    errors: list[str] = []
    allowed_top = {
        "display",
        "speaker",
        "power",
        "registry",
        "capability_query",
        "binwire",
        "rpp",
        "intent",
        "fastpath",
        "security",
        "native_jit",
        "units",
        "vector_clock_sync",
        "memory_compact",
        "version",
        "transaction_prepare",
        "transaction_commit",
    }

    for key in intent:
        if key not in allowed_top:
            errors.append(f"unsupported top-level key: {key}")

    display = intent.get("display")
    if isinstance(display, dict):
        _validate_display(display, errors)
    elif display is not None:
        errors.append("display must be an object")

    speaker = intent.get("speaker")
    if isinstance(speaker, dict):
        _validate_speaker(speaker, errors)
    elif speaker is not None:
        errors.append("speaker must be an object")

    power = intent.get("power")
    if isinstance(power, dict):
        _validate_power(power, errors)
    elif power is not None:
        errors.append("power must be an object")

    registry = intent.get("registry")
    if registry is not None and not isinstance(registry, dict):
        errors.append("registry must be an object")
    elif isinstance(registry, dict):
        errors.extend(validate_registry_payload(registry))
        errors.extend(_validate_registry_graph(registry))
        errors.extend(_validate_allocation_handles(_collect_units_dict(registry)))
        errors.extend(_validate_execution_core_units(_collect_units_dict(registry)))
        errors.extend(
            HostSchedulerCompiler.validate_priority_fields(_collect_units_dict(registry))
        )

    # Support legacy/top-level units blocks from vibe payloads
    units = intent.get("units")
    if isinstance(units, dict):
        errors.extend(validate_bus_multiplexing({"units": units}))
        errors.extend(validate_jit_units(units))
        errors.extend(_validate_units_graph(units))
        errors.extend(_validate_allocation_handles(units))
        errors.extend(_validate_execution_core_units(units))
        errors.extend(HostSchedulerCompiler.validate_priority_fields(units))

    if "memory_compact" in intent and not isinstance(intent["memory_compact"], bool):
        errors.append("memory_compact must be a boolean")

    if "transaction_commit" in intent and not isinstance(intent["transaction_commit"], bool):
        errors.append("transaction_commit must be a boolean")

    transaction_prepare = intent.get("transaction_prepare")
    if transaction_prepare is not None and not isinstance(transaction_prepare, dict):
        errors.append("transaction_prepare must be an object")

    native_jit = intent.get("native_jit")
    if native_jit is not None and not isinstance(native_jit, dict):
        errors.append("native_jit must be an object")
    elif isinstance(native_jit, dict):
        errors.extend(validate_native_jit_block(native_jit))

    if "capability_query" in intent and not isinstance(intent["capability_query"], bool):
        errors.append("capability_query must be a boolean")

    if "fastpath" in intent and not isinstance(intent["fastpath"], bool):
        errors.append("fastpath must be a boolean")

    intent_block = intent.get("intent")
    if intent_block is not None and not isinstance(intent_block, dict):
        errors.append("intent must be an object")
    elif isinstance(intent_block, dict):
        errors.extend(_validate_vibe_intent_block(intent_block))

    sync = intent.get("vector_clock_sync")
    if sync is not None and not isinstance(sync, dict):
        errors.append("vector_clock_sync must be an object")
    elif isinstance(sync, dict):
        for node, value in sync.items():
            if not isinstance(node, str) or not isinstance(value, int):
                errors.append("vector_clock_sync values must be string node IDs mapped to integers")
                break

    security = intent.get("security")
    if security is not None and not isinstance(security, dict):
        errors.append("security must be an object")
    elif isinstance(security, dict):
        if "signature_hex" in security and not isinstance(security["signature_hex"], str):
            errors.append("security.signature_hex must be a string")
        if "timestamp_epoch" in security and not isinstance(security["timestamp_epoch"], int):
            errors.append("security.timestamp_epoch must be an integer")

    errors.extend(verify_intent_signature(intent))
    errors.extend(
        require_signature_for_registry(intent, enabled=require_registry_signature)
    )
    errors.extend(validate_intent_safety(intent))
    return errors


def _validate_display(display: dict[str, Any], errors: list[str]) -> None:
    text = display.get("text")
    if text is None:
        return
    if not isinstance(text, dict):
        errors.append("display.text must be an object")
        return
    if "payload" in text and not isinstance(text["payload"], str):
        errors.append("display.text.payload must be a string")
    for int_field in ("x", "y", "size", "color"):
        if int_field in text and not isinstance(text[int_field], int):
            errors.append(f"display.text.{int_field} must be an integer")


def _validate_speaker(speaker: dict[str, Any], errors: list[str]) -> None:
    tone = speaker.get("tone")
    if tone is None:
        return
    if not isinstance(tone, dict):
        errors.append("speaker.tone must be an object")
        return
    if "frequency" in tone and not isinstance(tone["frequency"], (int, float)):
        errors.append("speaker.tone.frequency must be a number")
    for int_field in ("duration", "channel"):
        if int_field in tone and not isinstance(tone[int_field], int):
            errors.append(f"speaker.tone.{int_field} must be an integer")


def _validate_power(power: dict[str, Any], errors: list[str]) -> None:
    if "led" in power and not isinstance(power["led"], int):
        errors.append("power.led must be an integer")
    if "off" in power and not isinstance(power["off"], bool):
        errors.append("power.off must be a boolean")


def _validate_vibe_intent_block(intent_block: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    action = intent_block.get("action")
    if action is not None and not isinstance(action, str):
        errors.append("intent.action must be a string")
    if action == "fast_track_gpio":
        params = intent_block.get("parameters")
        if not isinstance(params, dict):
            errors.append("intent.parameters must be an object for fast_track_gpio")
        else:
            for field in ("unit_id", "pin"):
                if field in params and not isinstance(params[field], int):
                    errors.append(f"intent.parameters.{field} must be an integer")
            for field in ("frequency_hz", "frequency", "state_mask", "state_flag"):
                if field in params and not isinstance(params[field], int):
                    errors.append(f"intent.parameters.{field} must be an integer")
    elif action == "rpp_execute":
        params = intent_block.get("parameters")
        if not isinstance(params, dict):
            errors.append("intent.parameters must be an object for rpp_execute")
        else:
            for field in ("unit_id", "opcode", "functional_opcode", "data_vector", "parameter", "sequence_id"):
                if field in params and not isinstance(params[field], int):
                    errors.append(f"intent.parameters.{field} must be an integer")
    return errors


def _collect_units_dict(registry: dict[str, Any]) -> dict[str, dict[str, Any]]:
    units = registry.get("units")
    if isinstance(units, dict):
        return {k: v for k, v in units.items() if isinstance(v, dict)}
    if isinstance(units, list):
        return {
            record["unit_id"]: record
            for record in units
            if isinstance(record, dict) and "unit_id" in record
        }
    return {}


def _validate_registry_graph(registry: dict[str, Any]) -> list[str]:
    units = _collect_units_dict(registry)
    if not units:
        return []
    graph = StateGraphEngine.from_units(units)
    return graph.validate_dag()


def _validate_units_graph(units: dict[str, Any]) -> list[str]:
    unit_map = {k: v for k, v in units.items() if isinstance(v, dict)}
    if not unit_map:
        return []
    graph = StateGraphEngine.from_units(unit_map)
    return graph.validate_dag()


def _validate_allocation_handles(units: dict[str, dict[str, Any]]) -> list[str]:
    if not units:
        return []
    return HostMemoryProfiler().evaluate_registry_units(units)


def _validate_execution_core_units(units: dict[str, dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    for unit_id, unit_cfg in units.items():
        if isinstance(unit_cfg, dict):
            errors.extend(validate_execution_core_unit(unit_id, unit_cfg))
    return errors
