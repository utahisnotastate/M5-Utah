from m5resolver.validation import validate_intent_payload


def test_valid_intent_has_no_errors():
    payload = {
        "display": {"text": {"x": 0, "y": 0, "size": 2, "color": 65535, "payload": "ok"}},
        "speaker": {"tone": {"frequency": 440, "duration": 50, "channel": 0}},
        "power": {"led": 10, "off": False},
    }
    assert validate_intent_payload(payload) == []


def test_invalid_intent_reports_errors():
    payload = {
        "invalid": True,
        "display": {"text": {"x": "left", "payload": 123}},
        "speaker": {"tone": {"frequency": "high"}},
    }
    errors = validate_intent_payload(payload)
    assert any("unsupported top-level key: invalid" in e for e in errors)
    assert any("display.text.x must be an integer" in e for e in errors)
    assert any("display.text.payload must be a string" in e for e in errors)
    assert any("speaker.tone.frequency must be a number" in e for e in errors)
