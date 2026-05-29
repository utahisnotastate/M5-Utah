from m5resolver.simulation import HardwareSimulator


def test_simulation_rejects_high_power_intent():
    sim = HardwareSimulator(max_power_ma=100)
    intent = {
        "display": {"clear": True},
        "speaker": {"tone": {"frequency": 440, "duration": 100, "channel": 0}},
        "registry": {"units": {f"u{i}": {"frequency_hz": 50} for i in range(8)}},
    }
    errors = sim.simulate_intent(intent)
    assert errors
