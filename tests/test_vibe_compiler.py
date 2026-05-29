from m5resolver.vibe_compiler import compile_vibe_to_intent
from m5resolver.validation import validate_intent_payload


def test_compile_blink_prompt():
    intent = compile_vibe_to_intent("blink the led fast when tilt detected")
    assert "registry" in intent or "speaker" in intent
    assert validate_intent_payload(intent) == []
