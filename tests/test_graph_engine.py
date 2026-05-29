from m5resolver.graph_engine import StateGraphEngine


def test_mutation_cascade_follows_dependencies():
    graph = StateGraphEngine()
    graph.add_reactive_unit("imu_sensor_core", {"type": "hardware_driver", "pins": [21, 22]})
    graph.add_reactive_unit(
        "dsp_filter_unit",
        {"type": "virtual_dsp", "frequency_hz": 100, "slot_id": 1},
        depends_on=["imu_sensor_core"],
    )
    graph.add_reactive_unit(
        "pwm_actuator_output",
        {"type": "hardware_pwm", "pins": [13], "slot_id": 2},
        depends_on=["dsp_filter_unit"],
    )

    cascade = graph.compute_mutation_delta_paths("imu_sensor_core")
    assert cascade == ["imu_sensor_core", "dsp_filter_unit", "pwm_actuator_output"]


def test_minimal_patch_only_includes_cascade():
    units = {
        "imu_sensor_core": {"frequency_hz": 10, "slot_id": 0},
        "dsp_filter_unit": {"frequency_hz": 20, "slot_id": 1, "depends_on": ["imu_sensor_core"]},
        "other_unit": {"frequency_hz": 5, "slot_id": 3},
    }
    graph = StateGraphEngine.from_units(units)
    patch = graph.minimal_units_patch("imu_sensor_core", units)
    assert "imu_sensor_core" in patch
    assert "dsp_filter_unit" in patch
    assert "other_unit" not in patch
