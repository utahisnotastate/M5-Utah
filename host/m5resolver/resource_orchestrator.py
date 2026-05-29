from __future__ import annotations

import logging
from enum import IntEnum
from typing import Any

logger = logging.getLogger("m5resolver.orchestrator")

ELEVATED_HEAP_THRESHOLD = 28_000
CRITICAL_HEAP_THRESHOLD = 22_000


class ResourcePressureLevel(IntEnum):
    NOMINAL = 0
    ELEVATED = 1
    CRITICAL = 2


class HostResourceOrchestrator:
    """
    Predictive resource arbitration for host-side intent transmission.
    Mirrors firmware ResourceOrchestrator pressure evaluation.
    """

    def __init__(
        self,
        *,
        elevated_heap_threshold: int = ELEVATED_HEAP_THRESHOLD,
        critical_heap_threshold: int = CRITICAL_HEAP_THRESHOLD,
    ) -> None:
        self.elevated_heap_threshold = elevated_heap_threshold
        self.critical_heap_threshold = critical_heap_threshold
        self.last_pressure = ResourcePressureLevel.NOMINAL
        self.deferred_transmit_count = 0

    def evaluate_telemetry(self, telemetry: dict[str, Any]) -> ResourcePressureLevel:
        metrics = telemetry.get("metrics", {})
        free_heap = metrics.get("free_heap", 0)
        if not isinstance(free_heap, int):
            free_heap = 0

        orchestrator_level = metrics.get("orchestrator_pressure_level")
        if isinstance(orchestrator_level, int):
            self.last_pressure = ResourcePressureLevel(orchestrator_level)
            return self.last_pressure

        if free_heap < self.critical_heap_threshold:
            self.last_pressure = ResourcePressureLevel.CRITICAL
        elif free_heap < self.elevated_heap_threshold:
            self.last_pressure = ResourcePressureLevel.ELEVATED
        else:
            self.last_pressure = ResourcePressureLevel.NOMINAL
        return self.last_pressure

    def should_defer_intent(self, intent: dict[str, Any]) -> bool:
        if self.last_pressure != ResourcePressureLevel.CRITICAL:
            return False
        if "registry" in intent or "native_jit" in intent or "memory_compact" in intent:
            return False
        if intent.keys() <= {"security"}:
            return False
        return True

    def preflight_transmit(self, intent: dict[str, Any], *, free_heap: int) -> list[str]:
        self.evaluate_telemetry({"metrics": {"free_heap": free_heap}})
        if self.should_defer_intent(intent):
            self.deferred_transmit_count += 1
            logger.warning(
                "[ORCHESTRATOR] Deferring non-critical intent while device pressure=%s",
                self.last_pressure.name,
            )
            return [
                f"orchestrator_deferred: device heap {free_heap}B pressure "
                f"{self.last_pressure.name.lower()}"
            ]
        return []

    @staticmethod
    def is_critical_intent(intent: dict[str, Any]) -> bool:
        return any(key in intent for key in ("registry", "native_jit", "memory_compact"))
