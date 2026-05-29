from __future__ import annotations

import logging
import os
import sys
from typing import Any

logger = logging.getLogger("m5resolver.dashboard")

HEAP_REFERENCE_BYTES = 280_000
DEFAULT_TYPESTATE = "IDLE"


class TerminalStateVisualizer:
    """
    Real-time structural state visualizer (Feature 66).

    Transforms multi-core telemetry, memory maps, and bus allocation signals
    into a scannable terminal dashboard for development velocity.
    """

    @staticmethod
    def normalize_snapshot(metrics_snapshot: dict[str, Any] | None) -> dict[str, Any]:
        source = metrics_snapshot or {}
        active_unit = source.get("active_unit")
        if active_unit is None:
            active_unit_label = "N/A"
        else:
            active_unit_label = str(active_unit)

        free_heap_raw = source.get("free_heap_bytes", source.get("free_heap", 0))
        try:
            free_heap = max(0, int(free_heap_raw))
        except (TypeError, ValueError):
            free_heap = 0

        jitter_raw = source.get("task_jitter_ms", source.get("jitter_ms", 0))
        try:
            task_jitter_ms = max(0, int(jitter_raw))
        except (TypeError, ValueError):
            task_jitter_ms = 0

        typestate = str(source.get("typestate") or DEFAULT_TYPESTATE).upper()
        i2c_locked = bool(source.get("i2c_locked", False))
        core0_state = str(source.get("core0_state", "RUNNING"))
        core1_state = str(source.get("core1_state", "DETERMINISTIC ACTIVE"))

        return {
            "active_unit": active_unit_label,
            "free_heap_bytes": free_heap,
            "task_jitter_ms": task_jitter_ms,
            "typestate": typestate,
            "i2c_locked": i2c_locked,
            "core0_state": core0_state,
            "core1_state": core1_state,
        }

    @classmethod
    def snapshot_from_vitals(
        cls,
        unit_id: int | None,
        free_heap_bytes: int,
        task_jitter_ms: int,
        *,
        typestate: str | None = None,
        i2c_locked: bool | None = None,
    ) -> dict[str, Any]:
        return cls.normalize_snapshot(
            {
                "active_unit": unit_id,
                "free_heap_bytes": free_heap_bytes,
                "task_jitter_ms": task_jitter_ms,
                "typestate": typestate,
                "i2c_locked": i2c_locked,
            }
        )

    @classmethod
    def render_system_matrix(
        cls,
        metrics_snapshot: dict[str, Any] | None,
        *,
        clear_screen: bool = True,
    ) -> None:
        metrics = cls.normalize_snapshot(metrics_snapshot)
        if clear_screen:
            os.system("cls" if os.name == "nt" else "clear")

        print("=" * 70)
        print(" m5-utah // REAL-TIME PHYSICAL REGISTER & APPLICATION SURFACE ")
        print("=" * 70)

        print(f"[{'CORE 0: PROTOCOL ENG':^31}] | [{'CORE 1: APPLICATION ENG':^32}]")
        print(f" State: {metrics['core0_state']:<24} |  State: {metrics['core1_state']}")
        print(
            f" Stream: Ingesting fluxwire.py   |  Active Unit: Slot ID {metrics['active_unit']}"
        )
        print("-" * 70)

        free_heap = metrics["free_heap_bytes"]
        heap_percentage = max(0, min(100, int((free_heap / HEAP_REFERENCE_BYTES) * 100)))
        filled = heap_percentage // 5
        heap_bar = "█" * filled + "░" * (20 - filled)

        print(" SYSTEM HEADROOM METRICS:")
        print(
            f"  Executable IRAM Heap : {free_heap:6d} Bytes [{heap_bar}] {heap_percentage}%"
        )
        print(f"  Scheduling Jitter    : {metrics['task_jitter_ms']:3d} ms")
        print("-" * 70)

        lock_label = "[ LOCKED ]" if metrics["i2c_locked"] else "[ UNLOCKED ]"
        print(" ACTIVE PERIPHERAL LOCK BOUNDARIES:")
        print(f"  Shared I2C/SPI Mutex : {lock_label}")
        print(f"  Typestate Sequence   : {metrics['typestate']}")
        print("=" * 70)
        sys.stdout.flush()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    mock_metrics = {
        "active_unit": 7,
        "free_heap_bytes": 194200,
        "task_jitter_ms": 4,
        "i2c_locked": True,
        "typestate": "BUSY",
    }
    TerminalStateVisualizer.render_system_matrix(mock_metrics)
