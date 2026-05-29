from __future__ import annotations

import copy
import logging
from typing import Any

logger = logging.getLogger("m5resolver.optimizer")

DEFAULT_AVAILABLE_HEAP = 32_000
HEADROOM_RATIO = 0.40
MIN_BUFFER_BYTES = 64
MIN_FREQUENCY_HZ = 1


class HardwareCostModel:
    """
    Proactive intent pruning based on deterministic RAM cost estimates.

    Downsamples frequency and buffer sizes when projected draw exceeds
    the configured heap headroom before configs reach device firmware.
    """

    @staticmethod
    def estimate_ram_draw(frequency_hz: int, buffer_size_bytes: int) -> int:
        return buffer_size_bytes * 2 + (frequency_hz * 4)

    @staticmethod
    def evaluate_and_prune_intent(
        intent_unit: dict[str, Any],
        available_heap_bytes: int,
    ) -> tuple[dict[str, Any], bool]:
        pruned_unit = dict(intent_unit)
        is_pruned = False

        frequency = int(pruned_unit.get("frequency_hz", 1000))
        buffer_size = int(pruned_unit.get("buffer_size_bytes", 512))

        estimated_ram_draw = HardwareCostModel.estimate_ram_draw(frequency, buffer_size)
        safety_budget = int(available_heap_bytes * HEADROOM_RATIO)

        if estimated_ram_draw > safety_budget:
            logger.warning(
                "[PRUNER] Intent allocation (%sB) exceeds safety budget (%sB). "
                "Throttling frequency vectors...",
                estimated_ram_draw,
                safety_budget,
            )
            pruned_unit["frequency_hz"] = max(MIN_FREQUENCY_HZ, int(frequency * 0.25))
            pruned_unit["buffer_size_bytes"] = max(MIN_BUFFER_BYTES, int(buffer_size * 0.5))
            pruned_unit["pruned_by_gatekeeper"] = True
            is_pruned = True

        return pruned_unit, is_pruned

    @staticmethod
    def prune_registry_units(
        units: dict[str, Any], available_heap_bytes: int
    ) -> tuple[dict[str, Any], bool]:
        pruned_units: dict[str, Any] = {}
        any_pruned = False
        for unit_id, cfg in units.items():
            if not isinstance(cfg, dict):
                pruned_units[unit_id] = cfg
                continue
            optimized, was_pruned = HardwareCostModel.evaluate_and_prune_intent(
                cfg, available_heap_bytes
            )
            pruned_units[unit_id] = optimized
            any_pruned = any_pruned or was_pruned
        return pruned_units, any_pruned

    @staticmethod
    def prune_intent(
        intent: dict[str, Any], available_heap_bytes: int = DEFAULT_AVAILABLE_HEAP
    ) -> tuple[dict[str, Any], bool]:
        """Prune all unit blocks inside a full intent payload."""
        pruned = copy.deepcopy(intent)
        any_pruned = False

        registry = pruned.get("registry")
        if isinstance(registry, dict):
            units = registry.get("units")
            if isinstance(units, dict):
                optimized, was_pruned = HardwareCostModel.prune_registry_units(
                    units, available_heap_bytes
                )
                registry["units"] = optimized
                any_pruned = any_pruned or was_pruned

        top_units = pruned.get("units")
        if isinstance(top_units, dict):
            optimized, was_pruned = HardwareCostModel.prune_registry_units(
                top_units, available_heap_bytes
            )
            pruned["units"] = optimized
            any_pruned = any_pruned or was_pruned

        if any_pruned:
            pruned["resource_pruned"] = True

        return pruned, any_pruned
