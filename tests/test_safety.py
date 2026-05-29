from m5resolver.safety import validate_intent_safety, validate_registry_safety


def test_intent_safety_rejects_extreme_frequency():
    intent = {"speaker": {"tone": {"frequency": 99999, "duration": 50, "channel": 0}}}
    errors = validate_intent_safety(intent)
    assert any("frequency" in e for e in errors)


def test_registry_safety_rejects_too_many_units():
    registry = {"units": [{"unit_id": f"u{i}", "frequency_hz": 1} for i in range(20)]}
    errors = validate_registry_safety(registry)
    assert any("max units" in e for e in errors)
