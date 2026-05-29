from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("m5resolver.profiler")

DEFAULT_HANDLE_POOL_BYTES = 2048
COMPACTION_THRESHOLD_RATIO = 0.9
MAX_HANDLE_SLOT = 31


class HostMemoryProfiler:
    """
    Asymmetric heap tracking — simulates firmware handle-pool footprint from telemetry
    and registry unit buffer declarations before pushing state changes.
    """

    def __init__(self, memory_pool_limit_bytes: int = DEFAULT_HANDLE_POOL_BYTES) -> None:
        self.pool_limit = memory_pool_limit_bytes
        self.estimated_fragmentation_index = 0.0
        self.estimated_pool_top = 0
        self.device_free_heap = 0

    def update_device_snapshot(self, telemetry: dict[str, Any]) -> None:
        metrics = telemetry.get("metrics", {})
        if isinstance(metrics, dict):
            free_heap = metrics.get("free_heap")
            if isinstance(free_heap, int):
                self.device_free_heap = free_heap
            pool_top = metrics.get("handle_pool_top")
            if isinstance(pool_top, int):
                self.estimated_pool_top = pool_top
            frag = metrics.get("handle_fragmentation_index")
            if isinstance(frag, (int, float)):
                self.estimated_fragmentation_index = float(frag)

    def estimate_unit_buffer_bytes(self, unit: dict[str, Any]) -> int:
        return int(unit.get("buffer_size_bytes", 128))

    def projected_pool_top(self, units: dict[str, dict[str, Any]]) -> int:
        total = self.estimated_pool_top
        for unit in units.values():
            if isinstance(unit, dict):
                total += self.estimate_unit_buffer_bytes(unit)
        return total

    def evaluate_payload_safety(
        self, next_intent_unit: dict[str, Any], current_device_heap_top: int | None = None
    ) -> bool:
        buffer_requirement = self.estimate_unit_buffer_bytes(next_intent_unit)
        heap_top = (
            current_device_heap_top
            if current_device_heap_top is not None
            else self.estimated_pool_top
        )
        projected_heap_top = heap_top + buffer_requirement

        logger.info(
            "[PROFILER] Pre-flight memory audit: Projected Top=%sB / Limit=%sB",
            projected_heap_top,
            self.pool_limit,
        )

        if projected_heap_top > int(self.pool_limit * COMPACTION_THRESHOLD_RATIO):
            logger.error(
                "[CRITICAL DEFLECTION] Intent payload risks heap overflow! "
                "Postponing push event for compaction sequencing."
            )
            return False
        return True

    def evaluate_registry_units(self, units: dict[str, dict[str, Any]]) -> list[str]:
        errors: list[str] = []
        projected = self.projected_pool_top(units)
        if projected > int(self.pool_limit * COMPACTION_THRESHOLD_RATIO):
            errors.append(
                f"registry projected handle pool top {projected}B exceeds "
                f"{int(COMPACTION_THRESHOLD_RATIO * 100)}% of {self.pool_limit}B limit"
            )

        seen_handles: set[int] = set()
        for unit_id, unit in units.items():
            if not isinstance(unit, dict):
                continue
            handle_id = unit.get("allocation_handle_id")
            if handle_id is None:
                continue
            if not isinstance(handle_id, int) or handle_id < 0 or handle_id > MAX_HANDLE_SLOT:
                errors.append(
                    f"unit {unit_id} allocation_handle_id must be integer 0-{MAX_HANDLE_SLOT}"
                )
                continue
            if handle_id in seen_handles:
                errors.append(f"duplicate allocation_handle_id {handle_id} for unit {unit_id}")
            seen_handles.add(handle_id)
        return errors

    def should_request_compaction(self, units: dict[str, dict[str, Any]] | None = None) -> bool:
        projected = self.projected_pool_top(units or {})
        return projected > int(self.pool_limit * COMPACTION_THRESHOLD_RATIO)

    def compaction_intent(self) -> dict[str, Any]:
        return {"memory_compact": True}
