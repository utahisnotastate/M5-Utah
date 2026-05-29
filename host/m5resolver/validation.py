from __future__ import annotations

from typing import Any

from .bus_validation import validate_bus_multiplexing
from .safety import validate_intent_safety


class IntentValidator:
    """Strict validator that raises on first error batch (for tests and gates)."""

    def validate_intent_payload(self, intent: dict[str, Any]) -> None:
        errors = validate_intent_payload(intent)
        if errors:
            raise ValueError("; ".join(errors))

    def validate_registry(self, registry: dict[str, Any]) -> None:
        errors = validate_registry_payload(registry)
        if errors:
            raise ValueError("; ".join(errors))


def validate_registry_payload(registry: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    errors.extend(validate_intent_safety({"registry": registry}))
    errors.extend(validate_bus_multiplexing(registry))
    return errors


def validate_intent_payload(intent: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    allowed_top = {"display", "speaker", "power", "registry", "capability_query"}

    for key in intent:
        if key not in allowed_top:
            errors.append(f"unsupported top-level key: {key}")

    display = intent.get("display")
    if isinstance(display, dict):
        _validate_display(display, errors)
    elif display is not None:
        errors.append("display must be an object")

    speaker = intent.get("speaker")
    if isinstance(speaker, dict):
        _validate_speaker(speaker, errors)
    elif speaker is not None:
        errors.append("speaker must be an object")

    power = intent.get("power")
    if isinstance(power, dict):
        _validate_power(power, errors)
    elif power is not None:
        errors.append("power must be an object")

    registry = intent.get("registry")
    if registry is not None and not isinstance(registry, dict):
        errors.append("registry must be an object")
    elif isinstance(registry, dict):
        errors.extend(validate_registry_payload(registry))

    # Support legacy/top-level units blocks from vibe payloads
    units = intent.get("units")
    if isinstance(units, dict):
        errors.extend(validate_bus_multiplexing({"units": units}))

    if "capability_query" in intent and not isinstance(intent["capability_query"], bool):
        errors.append("capability_query must be a boolean")

    errors.extend(validate_intent_safety(intent))
    return errors


def _validate_display(display: dict[str, Any], errors: list[str]) -> None:
    text = display.get("text")
    if text is None:
        return
    if not isinstance(text, dict):
        errors.append("display.text must be an object")
        return
    if "payload" in text and not isinstance(text["payload"], str):
        errors.append("display.text.payload must be a string")
    for int_field in ("x", "y", "size", "color"):
        if int_field in text and not isinstance(text[int_field], int):
            errors.append(f"display.text.{int_field} must be an integer")


def _validate_speaker(speaker: dict[str, Any], errors: list[str]) -> None:
    tone = speaker.get("tone")
    if tone is None:
        return
    if not isinstance(tone, dict):
        errors.append("speaker.tone must be an object")
        return
    if "frequency" in tone and not isinstance(tone["frequency"], (int, float)):
        errors.append("speaker.tone.frequency must be a number")
    for int_field in ("duration", "channel"):
        if int_field in tone and not isinstance(tone[int_field], int):
            errors.append(f"speaker.tone.{int_field} must be an integer")


def _validate_power(power: dict[str, Any], errors: list[str]) -> None:
    if "led" in power and not isinstance(power["led"], int):
        errors.append("power.led must be an integer")
    if "off" in power and not isinstance(power["off"], bool):
        errors.append("power.off must be a boolean")
