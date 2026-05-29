from __future__ import annotations

import copy
import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .graph_engine import StateGraphEngine

logger = logging.getLogger("m5resolver.scheduler")

TIER_STANDARD = 1
TIER_ELEVATED = 2
TIER_REALTIME = 3
MAX_PRIORITY_TIER = 3


@dataclass
class SchedulingAudit:
    """Predictive scheduling preflight result before hardware transmit."""

    escalations: list[str] = field(default_factory=list)
    bus_conflicts: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


class HostSchedulerCompiler:
    """
    Proactive priority-inheritance mapping (Feature 58).

    Reverse-topology aware pin and bus contention analysis; injects
    assigned_priority_tier before registry deployment.
    """

    @staticmethod
    def compute_priority_matrix(raw_intent_registry: dict[str, Any]) -> dict[str, Any]:
        optimized_registry = copy.deepcopy(raw_intent_registry)
        units = optimized_registry.get("units")
        if not isinstance(units, dict):
            return optimized_registry

        peripheral_resource_map: dict[int, str] = {}
        bus_resource_map: dict[str, str] = {}
        audit = SchedulingAudit()

        for name, configurations in units.items():
            if not isinstance(configurations, dict):
                continue

            pin_list = HostSchedulerCompiler._extract_pins(configurations)
            is_critical = bool(configurations.get("realtime_critical", False))
            configurations.setdefault("assigned_priority_tier", TIER_STANDARD)

            bus_key = HostSchedulerCompiler._bus_resource_key(configurations)
            if bus_key is not None:
                if bus_key in bus_resource_map:
                    shared_owner = bus_resource_map[bus_key]
                    msg = (
                        f"Shared bus contention between '{name}' and '{shared_owner}' "
                        f"on {bus_key}"
                    )
                    audit.bus_conflicts.append(msg)
                    logger.warning("[SCHEDULER CONFLICT] %s", msg)
                    HostSchedulerCompiler._maybe_escalate_pair(
                        name,
                        shared_owner,
                        units,
                        configurations,
                        audit,
                        force=is_critical
                        or bool(units.get(shared_owner, {}).get("realtime_critical", False)),
                    )
                else:
                    bus_resource_map[bus_key] = name

            for pin in pin_list:
                if pin in peripheral_resource_map:
                    shared_owner = peripheral_resource_map[pin]
                    logger.warning(
                        "[SCHEDULER CONFLICT] Shared peripheral pin contention spotted "
                        "between '%s' and '%s'.",
                        name,
                        shared_owner,
                    )
                    owner_cfg = units.get(shared_owner)
                    owner_critical = (
                        bool(owner_cfg.get("realtime_critical", False))
                        if isinstance(owner_cfg, dict)
                        else False
                    )
                    HostSchedulerCompiler._maybe_escalate_pair(
                        name,
                        shared_owner,
                        units,
                        configurations,
                        audit,
                        force=is_critical or owner_critical,
                    )
                else:
                    peripheral_resource_map[pin] = name

            if is_critical and configurations.get("assigned_priority_tier", TIER_STANDARD) < TIER_REALTIME:
                configurations["assigned_priority_tier"] = TIER_REALTIME

        HostSchedulerCompiler._propagate_dependency_tiers(units, audit)
        return optimized_registry

    @staticmethod
    def _maybe_escalate_pair(
        name: str,
        shared_owner: str,
        units: dict[str, dict[str, Any]],
        configurations: dict[str, Any],
        audit: SchedulingAudit,
        *,
        force: bool,
    ) -> None:
        owner_cfg = units.get(shared_owner)
        if force:
            logger.info(
                "[GATEKEEPER] Elevating execution tiers for '%s' and '%s' to prevent "
                "priority inversion stalls.",
                name,
                shared_owner,
            )
            configurations["assigned_priority_tier"] = TIER_REALTIME
            if isinstance(owner_cfg, dict):
                owner_cfg["assigned_priority_tier"] = TIER_REALTIME
            audit.escalations.append(f"{name}<->{shared_owner}:tier={TIER_REALTIME}")
        else:
            audit.warnings.append(
                f"Pin/bus overlap '{name}' vs '{shared_owner}' without realtime_critical — "
                "consider enabling gatekeeper tiers"
            )

    @staticmethod
    def _extract_pins(configurations: dict[str, Any]) -> list[int]:
        pins = configurations.get("pins", [])
        if isinstance(pins, list):
            return [int(p) for p in pins if isinstance(p, (int, float))]
        return []

    @staticmethod
    def _bus_resource_key(configurations: dict[str, Any]) -> str | None:
        bus = configurations.get("bus") or configurations.get("bus_type")
        if not isinstance(bus, str) or not bus.strip():
            return None
        normalized = bus.strip().lower()
        if normalized in {"internal", "virtual"}:
            return None
        address = configurations.get("address")
        if address is not None:
            return f"{normalized}:{int(address)}"
        return normalized

    @staticmethod
    def _propagate_dependency_tiers(units: dict[str, dict[str, Any]], audit: SchedulingAudit) -> None:
        """Elevate dependents when upstream units run at elevated tiers (reverse topo pass)."""
        graph = StateGraphEngine.from_units(units)
        if graph.has_cycle():
            return

        ordered: list[str] = []
        visited: set[str] = set()

        def visit(name: str) -> None:
            if name in visited or name not in graph.nodes:
                return
            visited.add(name)
            for dep in graph.nodes[name].dependencies:
                visit(dep)
            ordered.append(name)

        for unit_name in units:
            visit(unit_name)

        for name in ordered:
            cfg = units.get(name)
            node = graph.nodes.get(name)
            if not isinstance(cfg, dict) or node is None:
                continue
            dep_tiers = [
                int(units[dep].get("assigned_priority_tier", TIER_STANDARD))
                for dep in node.dependencies
                if dep in units and isinstance(units[dep], dict)
            ]
            if not dep_tiers:
                continue
            required = max(dep_tiers)
            current = int(cfg.get("assigned_priority_tier", TIER_STANDARD))
            if current < required:
                cfg["assigned_priority_tier"] = required
                audit.escalations.append(f"{name}:dependency_tier={required}")

    @staticmethod
    def predictive_scheduling_audit(intent: dict[str, Any]) -> SchedulingAudit:
        """Run compilation pass and collect escalation / contention telemetry."""
        audit = SchedulingAudit()
        before_units = HostSchedulerCompiler._extract_units_block(intent)
        if before_units is None:
            return audit

        for name, cfg in before_units.items():
            if not isinstance(cfg, dict):
                continue
            bus_key = HostSchedulerCompiler._bus_resource_key(cfg)
            if bus_key is None:
                continue
            for other_name, other_cfg in before_units.items():
                if other_name == name or not isinstance(other_cfg, dict):
                    continue
                if HostSchedulerCompiler._bus_resource_key(other_cfg) == bus_key:
                    audit.bus_conflicts.append(f"{name}<->{other_name}:{bus_key}")

        peripheral_resource_map: dict[int, str] = {}
        for name, cfg in before_units.items():
            if not isinstance(cfg, dict):
                continue
            for pin in HostSchedulerCompiler._extract_pins(cfg):
                if pin in peripheral_resource_map:
                    audit.warnings.append(f"pin {pin}: {name} vs {peripheral_resource_map[pin]}")
                else:
                    peripheral_resource_map[pin] = name

        after_intent = HostSchedulerCompiler.apply_to_intent(copy.deepcopy(intent))
        after_units = HostSchedulerCompiler._extract_units_block(after_intent) or {}

        for name, after_cfg in after_units.items():
            if not isinstance(after_cfg, dict):
                continue
            before_cfg = before_units.get(name, {})
            before_tier = int(before_cfg.get("assigned_priority_tier", TIER_STANDARD)) if isinstance(before_cfg, dict) else TIER_STANDARD
            after_tier = int(after_cfg.get("assigned_priority_tier", TIER_STANDARD))
            if after_tier > before_tier:
                audit.escalations.append(f"{name}:tier={after_tier}")

        return audit

    @staticmethod
    def _extract_units_block(intent: dict[str, Any]) -> dict[str, Any] | None:
        registry = intent.get("registry")
        if isinstance(registry, dict) and isinstance(registry.get("units"), dict):
            return registry["units"]
        units = intent.get("units")
        if isinstance(units, dict):
            return units
        return None

    @staticmethod
    def audit_registry_file(registry_path: str | Path) -> tuple[dict[str, Any], SchedulingAudit]:
        raw = json.loads(Path(registry_path).read_text(encoding="utf-8"))
        units_list = raw.get("units", [])
        units_dict = {
            record["unit_id"]: record
            for record in units_list
            if isinstance(record, dict) and "unit_id" in record
        }
        optimized = HostSchedulerCompiler.compute_priority_matrix({"units": units_dict})
        audit = HostSchedulerCompiler.predictive_scheduling_audit({"units": units_dict})
        return optimized, audit

    @staticmethod
    def tier_to_firmware_priority(tier: int) -> int:
        if tier >= TIER_REALTIME:
            return 6
        if tier == TIER_ELEVATED:
            return 4
        return 2

    @staticmethod
    def apply_to_intent(intent: dict[str, Any]) -> dict[str, Any]:
        compiled = copy.deepcopy(intent)
        registry = compiled.get("registry")
        if isinstance(registry, dict) and isinstance(registry.get("units"), dict):
            optimized = HostSchedulerCompiler.compute_priority_matrix(
                {"units": registry["units"]}
            )
            registry["units"] = optimized["units"]
            compiled["registry"] = registry
            return compiled

        top_units = compiled.get("units")
        if isinstance(top_units, dict):
            optimized = HostSchedulerCompiler.compute_priority_matrix({"units": top_units})
            compiled["units"] = optimized["units"]
        return compiled

    @staticmethod
    def compile_with_audit(intent: dict[str, Any]) -> tuple[dict[str, Any], SchedulingAudit]:
        audit = HostSchedulerCompiler.predictive_scheduling_audit(intent)
        compiled = HostSchedulerCompiler.apply_to_intent(intent)
        return compiled, audit

    @staticmethod
    def validate_priority_fields(units: dict[str, dict[str, Any]]) -> list[str]:
        errors: list[str] = []
        for unit_id, unit in units.items():
            if not isinstance(unit, dict):
                continue
            tier = unit.get("assigned_priority_tier")
            if tier is not None and (
                not isinstance(tier, int) or tier < 1 or tier > MAX_PRIORITY_TIER
            ):
                errors.append(
                    f"unit {unit_id} assigned_priority_tier must be integer 1-{MAX_PRIORITY_TIER}"
                )
            if "realtime_critical" in unit and not isinstance(unit["realtime_critical"], bool):
                errors.append(f"unit {unit_id} realtime_critical must be a boolean")
        return errors


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    sample_intent = {
        "units": {
            "high_speed_actuator": {"pins": [13], "realtime_critical": True},
            "background_logger": {"pins": [13], "realtime_critical": False},
        }
    }
    processed_output = HostSchedulerCompiler.compute_priority_matrix(sample_intent)
    logger.info(
        "Compiled scheduler mapping topology:\n%s",
        json.dumps(processed_output, indent=2),
    )
