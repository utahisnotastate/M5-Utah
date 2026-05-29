from m5resolver.scheduler_compiler import (
    TIER_REALTIME,
    TIER_STANDARD,
    HostSchedulerCompiler,
)


def test_compute_priority_matrix_no_conflict():
    registry = {
        "units": {
            "sensor_a": {"pins": [21, 22], "realtime_critical": False},
            "sensor_b": {"pins": [25, 26], "realtime_critical": False},
        }
    }
    result = HostSchedulerCompiler.compute_priority_matrix(registry)
    assert result["units"]["sensor_a"]["assigned_priority_tier"] == TIER_STANDARD
    assert result["units"]["sensor_b"]["assigned_priority_tier"] == TIER_STANDARD


def test_shared_pin_escalates_both_units():
    registry = {
        "units": {
            "motor_driver": {"pins": [12, 13], "realtime_critical": True},
            "status_monitor": {"pins": [13], "realtime_critical": False},
        }
    }
    result = HostSchedulerCompiler.compute_priority_matrix(registry)
    assert result["units"]["motor_driver"]["assigned_priority_tier"] == TIER_REALTIME
    assert result["units"]["status_monitor"]["assigned_priority_tier"] == TIER_REALTIME


def test_apply_to_intent_registry_block():
    intent = {
        "registry": {
            "units": {
                "spi_a": {"pins": [18], "realtime_critical": True},
                "spi_b": {"pins": [18], "realtime_critical": False},
            }
        }
    }
    compiled = HostSchedulerCompiler.apply_to_intent(intent)
    assert compiled["registry"]["units"]["spi_a"]["assigned_priority_tier"] == TIER_REALTIME
    assert compiled["registry"]["units"]["spi_b"]["assigned_priority_tier"] == TIER_REALTIME


def test_tier_to_firmware_priority_mapping():
    assert HostSchedulerCompiler.tier_to_firmware_priority(1) == 2
    assert HostSchedulerCompiler.tier_to_firmware_priority(2) == 4
    assert HostSchedulerCompiler.tier_to_firmware_priority(3) == 6
