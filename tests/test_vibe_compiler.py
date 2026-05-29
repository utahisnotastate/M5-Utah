from m5resolver.vibe_compiler import compile_vibe_to_intent
from m5resolver.validation import validate_intent_payload


def test_compile_blink_prompt():
    intent = compile_vibe_to_intent("blink the led fast when tilt detected")
    assert "registry" in intent or "speaker" in intent
    assert validate_intent_payload(intent) == []


def test_compile_gpio_pin_prompt_is_fastpath():
    intent = compile_vibe_to_intent("toggle gpio pin 21 at 100hz")
    assert intent["intent"]["action"] == "fast_track_gpio"
    assert intent["intent"]["parameters"]["pin"] == 21
    assert validate_intent_payload(intent) == []
