"""Tests for integrated m5-kernel host/firmware contract alignment."""

from m5resolver.controller import IntentController
from m5resolver.kernel_runtime import (
    CROSS_CORE_RING_BYTES,
    FAST_PATH_QUEUE_MIN_BYTES,
    M5_KERNEL_CORE_APPLICATION,
    M5_KERNEL_CORE_PROTOCOL,
)
from m5resolver.scheduler_compiler import HostSchedulerCompiler, TIER_REALTIME


def test_m5_integrated_kernel_contracts():
    """Host constants align with DualCoreHarness / CrossCorePipe firmware layout."""
    assert M5_KERNEL_CORE_PROTOCOL == 0
    assert M5_KERNEL_CORE_APPLICATION == 1
    assert FAST_PATH_QUEUE_MIN_BYTES <= CROSS_CORE_RING_BYTES


def test_scheduler_compiler_wires_through_controller_flag():
    assert IntentController.__init__.__defaults__ is not None
    # enable_scheduler_compilation defaults True in signature
    params = IntentController.__init__.__code__.co_varnames
    assert "enable_scheduler_compilation" in params


def test_scheduler_elevates_contested_spi_pins():
    contested = {
        "units": {
            "high_speed_spi_bus": {"pins": [18, 23], "realtime_critical": True},
            "ambient_logger": {"pins": [18], "realtime_critical": False},
        }
    }
    compiled = HostSchedulerCompiler.compute_priority_matrix(contested)
    assert compiled["units"]["high_speed_spi_bus"]["assigned_priority_tier"] == TIER_REALTIME
    assert compiled["units"]["ambient_logger"]["assigned_priority_tier"] == TIER_REALTIME


def test_scheduler_apply_to_intent_registry_block():
    intent = {
        "registry": {
            "units": {
                "motor": {"pins": [12], "realtime_critical": True},
                "sensor": {"pins": [12]},
            }
        }
    }
    compiled = HostSchedulerCompiler.apply_to_intent(intent)
    assert compiled["registry"]["units"]["motor"]["assigned_priority_tier"] == TIER_REALTIME
    assert compiled["registry"]["units"]["sensor"]["assigned_priority_tier"] == TIER_REALTIME


def test_m5_unified_lifecycle_boot_sequence():
    """Host documents the firmware unified boot order for m5IntegratedKernelBoot()."""
    from m5resolver.kernel_runtime import INTEGRATED_BOOT_SEQUENCE, UNIFIED_LIFECYCLE_STAGES

    assert INTEGRATED_BOOT_SEQUENCE[0] == "registryRuntimeInit"
    assert INTEGRATED_BOOT_SEQUENCE[-1] == "m5KernelApplicationCoreTask"
    assert "M5Kernel.start" in INTEGRATED_BOOT_SEQUENCE
    assert UNIFIED_LIFECYCLE_STAGES == (
        "compile",
        "validate",
        "transmit",
        "ingest",
        "orchestrate",
        "observe",
    )

