from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .graph_engine import StateGraphEngine
from .memory_compiler import (
    IRAM_EXEC_END,
    IRAM_EXEC_START,
    HardwareMemoryCompiler,
)


@dataclass(frozen=True)
class UnitSpec:
    unit_id: str
    bus: str
    address: int | None
    capabilities: list[str]
    register_map: dict[str, Any]
    bounty_id: str | None = None
    semantic_action: str | None = None
    frequency_hz: int | None = None
    max_power_ma: int | None = None
    refresh_sequence_id: int | None = None
    allocation_handle_id: int | None = None
    buffer_size_bytes: int | None = None
    realtime_critical: bool | None = None
    assigned_priority_tier: int | None = None
    execution_core_target: int | None = None
    buffer_allocation_bytes: int | None = None
    depends_on: tuple[str, ...] = ()


class DriverRegistry:
    """JSON-backed registry with DAG topology for dependency-aware mutations."""

    def __init__(self, registry_file: str | Path) -> None:
        self.registry_file = Path(registry_file)
        self._units: dict[str, UnitSpec] = {}
        self.graph = StateGraphEngine()
        self.last_graph_errors: list[str] = []

    def load(self) -> None:
        raw = json.loads(self.registry_file.read_text(encoding="utf-8"))
        units: dict[str, UnitSpec] = {}
        graph_units: dict[str, dict[str, Any]] = {}

        for record in raw.get("units", []):
            deps = record.get("depends_on", [])
            dep_tuple = tuple(deps) if isinstance(deps, list) else ()
            spec = UnitSpec(
                unit_id=record["unit_id"],
                bus=record["bus"],
                address=record.get("address"),
                capabilities=list(record.get("capabilities", [])),
                register_map=dict(record.get("register_map", {})),
                bounty_id=record.get("bounty_id"),
                semantic_action=record.get("semantic_action"),
                frequency_hz=record.get("frequency_hz"),
                max_power_ma=record.get("max_power_ma"),
                refresh_sequence_id=record.get("refresh_sequence_id"),
                allocation_handle_id=record.get("allocation_handle_id"),
                buffer_size_bytes=record.get("buffer_size_bytes"),
                realtime_critical=record.get("realtime_critical"),
                assigned_priority_tier=record.get("assigned_priority_tier"),
                execution_core_target=record.get("execution_core_target"),
                buffer_allocation_bytes=record.get("buffer_allocation_bytes"),
                depends_on=dep_tuple,
            )
            units[spec.unit_id] = spec
            graph_units[spec.unit_id] = record

        self._units = units
        self.graph = StateGraphEngine.from_units(graph_units)
        self.last_graph_errors = self.graph.validate_dag()

    def get(self, unit_id: str) -> UnitSpec | None:
        return self._units.get(unit_id)

    def list_ids(self) -> list[str]:
        return sorted(self._units.keys())

    def mutation_cascade_for(self, changed_node: str) -> list[str]:
        return self.graph.compute_mutation_delta_paths(changed_node)

    def minimal_patch_for(self, changed_node: str) -> dict[str, dict[str, Any]]:
        raw = json.loads(self.registry_file.read_text(encoding="utf-8"))
        units_list = raw.get("units", [])
        by_id = {
            record["unit_id"]: record
            for record in units_list
            if isinstance(record, dict) and "unit_id" in record
        }
        return self.graph.minimal_units_patch(changed_node, by_id)

    @staticmethod
    def graph_from_units_dict(units: dict[str, dict[str, Any]]) -> StateGraphEngine:
        return StateGraphEngine.from_units(units)

    def compile_overlay_for_unit(
        self, unit_id: str, *, default_address: int = IRAM_EXEC_START
    ) -> bytes | None:
        raw = json.loads(self.registry_file.read_text(encoding="utf-8"))
        for record in raw.get("units", []):
            if record.get("unit_id") != unit_id:
                continue
            if not isinstance(record, dict):
                return None
            try:
                return HardwareMemoryCompiler.compile_unit_overlay(
                    record, default_address=default_address
                )
            except ValueError:
                return None
        return None
