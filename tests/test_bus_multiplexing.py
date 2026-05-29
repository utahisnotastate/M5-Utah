from m5resolver.bus_validation import validate_bus_multiplexing
from m5resolver.validation import IntentValidator, validate_intent_payload


def test_dynamic_bus_multiplexing_pin_conflict():
    validator = IntentValidator()
    malformed_intent = {
        "registry": {
            "units": {
                "i2c_bus_override": {
                    "type": "I2C",
                    "pins": [21, 21],
                    "frequency_hz": 400000,
                }
            }
        }
    }
    try:
        validator.validate_intent_payload(malformed_intent)
        assert False, "expected ValueError"
    except ValueError as exc:
        assert "Pin conflict" in str(exc)


def test_top_level_units_bus_validation():
    payload = {
        "units": {
            "sensor_a": {"type": "I2C", "pins": [21, 22], "frequency_hz": 100000}
        }
    }
    assert validate_bus_multiplexing({"units": payload["units"]}) == []


def test_valid_i2c_in_registry_intent():
    payload = {
        "registry": {
            "units": {
                "external_env": {
                    "type": "I2C",
                    "pins": [21, 22],
                    "frequency_hz": 100000,
                    "address": 68,
                }
            }
        }
    }
    assert validate_intent_payload(payload) == []
