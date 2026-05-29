from __future__ import annotations

import re
from typing import Any


def compile_vibe_to_intent(prompt: str) -> dict[str, Any]:
    """
    Compiled-AI pipeline: map natural language to schema-safe intent JSON.
    Rule-based compiler (no runtime LLM dependency).
    """
    text = prompt.strip().lower()

    gpio_pin = _extract_gpio_pin(text)
    if gpio_pin is not None and any(
        word in text for word in ("blink", "gpio", "pin", "hz", "frequency", "mask")
    ):
        return {
            "intent": {
                "action": "fast_track_gpio",
                "parameters": {
                    "unit_id": _extract_unit_id(text) or 7,
                    "pin": gpio_pin,
                    "frequency_hz": min(65535, _extract_hz_value(text) or 50),
                    "state_mask": _extract_state_mask(text) or 412,
                },
            },
            "fastpath": True,
        }

    intent: dict[str, Any] = {"display": {}, "speaker": {}}

    if any(word in text for word in ("clear", "reset screen", "blank")):
        intent["display"]["clear"] = True
        intent["display"]["bg_color"] = 0

    if "red" in text:
        intent["display"].setdefault("text", {})
        intent["display"]["text"]["color"] = 0xF800
    elif "green" in text:
        intent["display"].setdefault("text", {})
        intent["display"]["text"]["color"] = 0x07E0
    elif "blue" in text:
        intent["display"].setdefault("text", {})
        intent["display"]["text"]["color"] = 0x001F

    if any(word in text for word in ("show", "display", "text", "message")):
        intent["display"].setdefault("text", {})
        intent["display"]["text"].setdefault("x", 8)
        intent["display"]["text"].setdefault("y", 24)
        intent["display"]["text"].setdefault("size", 2)
        intent["display"]["text"]["payload"] = _extract_message(prompt)

    if any(word in text for word in ("beep", "tone", "sound", "speaker", "alarm")):
        freq = 660.0
        if "high" in text:
            freq = 1200.0
        if "low" in text:
            freq = 300.0
        intent["speaker"]["tone"] = {"frequency": freq, "duration": 120, "channel": 0}

    if "stop" in text and "sound" in text:
        intent["speaker"] = {"stop": True}

    if any(word in text for word in ("tilt", "imu", "accel", "motion")):
        intent["registry"] = {
            "units": {
                "motion_reactive": {
                    "semantic_action": "ACTION_REACT_TO_MOTION",
                    "frequency_hz": 10,
                    "priority": 2,
                    "max_power_ma": 80,
                    "capabilities": ["accel"],
                }
            }
        }

    if any(word in text for word in ("blink", "led", "flash")):
        intent.setdefault("registry", {"units": {}})
        intent["registry"]["units"]["blink_unit"] = {
            "semantic_action": "ACTION_INDICATE_STATUS_SUCCESS",
            "frequency_hz": _extract_frequency(text),
            "priority": 1,
            "max_power_ma": 40,
        }

    if any(word in text for word in ("power off", "shutdown")):
        intent["power"] = {"off": True}

    if any(word in text for word in ("room", "enter", "presence")):
        intent["registry"] = {
            "units": {
                "presence_logic": {
                    "semantic_action": "ACTION_REACT_TO_MOTION",
                    "frequency_hz": 5,
                    "priority": 3,
                    "vibe_description": prompt,
                }
            }
        }
        intent["speaker"]["tone"] = {"frequency": 880.0, "duration": 80, "channel": 0}

    # Strip empty sections
    return {k: v for k, v in intent.items() if v}


def _extract_message(prompt: str) -> str:
    quoted = re.search(r"['\"](.+?)['\"]", prompt)
    if quoted:
        return quoted.group(1)
    return prompt[:48] if prompt else "Vibe OK"


def _extract_frequency(text: str) -> int:
    hz = _extract_hz_value(text)
    if hz is not None:
        return min(60, max(1, hz))
    if "fast" in text:
        return 8
    if "slow" in text:
        return 1
    return 2


def _extract_hz_value(text: str) -> int | None:
    match = re.search(r"(\d+)\s*hz", text)
    if match:
        return int(match.group(1))
    return None


def _extract_gpio_pin(text: str) -> int | None:
    for pattern in (r"gpio\s*(?:pin\s*)?(\d+)", r"pin\s*(\d+)"):
        match = re.search(pattern, text)
        if match:
            return min(255, int(match.group(1)))
    return None


def _extract_unit_id(text: str) -> int | None:
    match = re.search(r"unit\s*(?:id\s*)?(\d+)", text)
    if match:
        return min(255, int(match.group(1)))
    return None


def _extract_state_mask(text: str) -> int | None:
    match = re.search(r"(?:mask|state(?:\s*mask)?)\s*(\d+)", text)
    if match:
        return int(match.group(1))
    return None
