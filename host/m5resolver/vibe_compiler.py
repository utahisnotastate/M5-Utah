from __future__ import annotations

import re
from typing import Any


def compile_vibe_to_intent(prompt: str) -> dict[str, Any]:
    """
    Compiled-AI pipeline: map natural language to schema-safe intent JSON.
    Rule-based compiler (no runtime LLM dependency).
    """
    text = prompt.strip().lower()
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
    match = re.search(r"(\d+)\s*hz", text)
    if match:
        return min(60, max(1, int(match.group(1))))
    if "fast" in text:
        return 8
    if "slow" in text:
        return 1
    return 2
