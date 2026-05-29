from __future__ import annotations

import logging
from typing import Any

from .graph_engine import StateGraphEngine

logger = logging.getLogger("m5resolver.typestate")

VALID_TRANSITIONS: dict[str, frozenset[str]] = {
    "UNINITIALIZED": frozenset({"INITIALIZING", "SAFE_MODE"}),
    "INITIALIZING": frozenset({"IDLE", "SAFE_MODE"}),
    "IDLE": frozenset({"BUSY", "SUSPENDED", "SAFE_MODE"}),
    "BUSY": frozenset({"IDLE", "SAFE_MODE"}),
    "SUSPENDED": frozenset({"IDLE", "SAFE_MODE"}),
    "SAFE_MODE": frozenset({"UNINITIALIZED"}),
}


class SystemTypestateEnforcer:
    """
    Formal typestate state validation (Feature 65).

    Enforces mathematically valid structural transitions across the hardware mesh
    before deltas or registry mutations are serialized to the wire.
    """

    def __init__(self, transitions: dict[str, frozenset[str]] | None = None) -> None:
        self.valid_transitions = transitions or VALID_TRANSITIONS

    def verify_transition_legality(self, current_state: str, target_state: str) -> bool:
        current = current_state.upper()
        target = target_state.upper()
        allowed = self.valid_transitions.get(current)
        if allowed is None:
            logger.error("[TYPESTATE CRITICAL] Invalid system state detected: %s", current)
            return False
        is_valid = target in allowed
        if is_valid:
            logger.info("[TYPESTATE PASS] State transition verified: %s -> %s", current, target)
        else:
            logger.error(
                "[TYPESTATE VIOLATION] Refusing illegal transition: %s -> %s", current, target
            )
        return is_valid

    def validate_unit_transition(
        self,
        unit_id: str,
        current_state: str,
        target_state: str,
    ) -> list[str]:
        if self.verify_transition_legality(current_state, target_state):
            return []
        return [
            f"typestate_violation: unit {unit_id} cannot transition "
            f"{current_state.upper()} -> {target_state.upper()}"
        ]

    def validate_intent_typestate(self, intent: dict[str, Any]) -> list[str]:
        """Validate explicit typestate block and per-unit state transitions in registry."""
        errors: list[str] = []

        typestate_block = intent.get("typestate")
        if isinstance(typestate_block, dict):
            current = str(typestate_block.get("current", "IDLE"))
            target = str(typestate_block.get("target", current))
            if not self.verify_transition_legality(current, target):
                errors.append(f"typestate_violation: global {current} -> {target}")

        units = self._collect_units(intent)
        if units:
            graph = StateGraphEngine.from_units(units)
            errors.extend(graph.validate_dag())

        for unit_id, config in units.items():
            if not isinstance(config, dict):
                continue
            current = str(config.get("state", config.get("current_state", "IDLE")))
            if "target_state" in config:
                target = str(config["target_state"])
                errors.extend(self.validate_unit_transition(unit_id, current, target))

        return errors

    @staticmethod
    def _collect_units(intent: dict[str, Any]) -> dict[str, dict[str, Any]]:
        registry = intent.get("registry")
        if isinstance(registry, dict):
            units = registry.get("units")
            if isinstance(units, dict):
                return {str(k): v for k, v in units.items() if isinstance(v, dict)}
        units = intent.get("units")
        if isinstance(units, dict):
            return {str(k): v for k, v in units.items() if isinstance(v, dict)}
        return {}


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    enforcer = SystemTypestateEnforcer()
    assert enforcer.verify_transition_legality("BUSY", "INITIALIZING") is False
