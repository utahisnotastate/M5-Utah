from __future__ import annotations

"""Host mirror of firmware DualCoreHarness / Feature 52 constants."""

DUAL_CORE_PROTOCOL_ENGINE = 0
DUAL_CORE_APPLICATION_ENGINE = 1

DUAL_CORE_CAPABILITY = "dual_core_execution_harness"

FAST_PATH_QUEUE_MIN_BYTES = 512
CROSS_CORE_RING_BYTES = 8192

VALID_EXECUTION_CORE_TARGETS = frozenset({0, 1})


def validate_execution_core_unit(unit_id: str, unit_cfg: dict) -> list[str]:
    errors: list[str] = []
    core = unit_cfg.get("execution_core_target")
    if core is not None:
        if not isinstance(core, int) or core not in VALID_EXECUTION_CORE_TARGETS:
            errors.append(
                f"units.{unit_id}.execution_core_target must be 0 (protocol) or 1 (application)"
            )

    buffer_alloc = unit_cfg.get("buffer_allocation_bytes")
    if buffer_alloc is not None:
        if not isinstance(buffer_alloc, int) or buffer_alloc < FAST_PATH_QUEUE_MIN_BYTES:
            errors.append(
                f"units.{unit_id}.buffer_allocation_bytes must be >= {FAST_PATH_QUEUE_MIN_BYTES}"
            )
        if buffer_alloc > CROSS_CORE_RING_BYTES:
            errors.append(
                f"units.{unit_id}.buffer_allocation_bytes exceeds ring capacity "
                f"({CROSS_CORE_RING_BYTES})"
            )

    unit_type = unit_cfg.get("type")
    if unit_type == "fast_path_bridge":
        if core is None:
            errors.append(f"units.{unit_id}.type fast_path_bridge requires execution_core_target")
        if buffer_alloc is None:
            errors.append(
                f"units.{unit_id}.type fast_path_bridge requires buffer_allocation_bytes"
            )
    return errors
