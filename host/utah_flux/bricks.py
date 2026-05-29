from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class BrickSpec:
    brick_id: str
    label: str
    emoji: str
    category: str  # trigger | action | sensor | logic
    color: str
    description: str
    params: dict[str, dict[str, Any]]


BRICK_CATALOG: list[BrickSpec] = [
    BrickSpec(
        "when_start",
        "When Project Starts",
        "🚀",
        "trigger",
        "#4CAF50",
        "Runs once when you press Play",
        {},
    ),
    BrickSpec(
        "when_tilt",
        "When Device Tilts",
        "📐",
        "trigger",
        "#8BC34A",
        "Fires when you move or tilt the device",
        {"sensitivity": {"type": "number", "default": 0.3, "min": 0.1, "max": 2.0, "label": "Sensitivity"}},
    ),
    BrickSpec(
        "when_loud",
        "When It Gets Loud",
        "🔊",
        "trigger",
        "#CDDC39",
        "Fires on strong motion (shake)",
        {"threshold": {"type": "number", "default": 0.8, "min": 0.2, "max": 3.0, "label": "Shake Level"}},
    ),
    BrickSpec(
        "show_message",
        "Show Message",
        "💬",
        "action",
        "#2196F3",
        "Writes text on the screen",
        {
            "text": {"type": "text", "default": "Hello!", "label": "Message"},
            "color": {
                "type": "choice",
                "default": "green",
                "choices": ["green", "red", "blue", "yellow", "white"],
                "label": "Color",
            },
        },
    ),
    BrickSpec(
        "play_sound",
        "Play Sound",
        "🎵",
        "action",
        "#03A9F4",
        "Plays a beep or tone",
        {
            "pitch": {
                "type": "choice",
                "default": "medium",
                "choices": ["low", "medium", "high"],
                "label": "Pitch",
            },
            "length": {"type": "choice", "default": "short", "choices": ["short", "long"], "label": "Length"},
        },
    ),
    BrickSpec(
        "happy_blink",
        "Happy Blink",
        "✨",
        "action",
        "#00BCD4",
        "Blinks the screen green with a success sound",
        {},
    ),
    BrickSpec(
        "alert_alarm",
        "Alert Alarm",
        "🚨",
        "action",
        "#FF5722",
        "Red alert text and alarm sound",
        {},
    ),
    BrickSpec(
        "clear_screen",
        "Clear Screen",
        "🧹",
        "action",
        "#607D8B",
        "Clears the display",
        {},
    ),
    BrickSpec(
        "party_mode",
        "Party Mode",
        "🎉",
        "action",
        "#E91E63",
        "Colorful message and fun sounds",
        {},
    ),
    BrickSpec(
        "read_motion",
        "Read Motion",
        "📡",
        "sensor",
        "#9C27B0",
        "Shows live tilt values on screen",
        {},
    ),
    BrickSpec(
        "safe_mode",
        "Safe Mode",
        "🛡️",
        "logic",
        "#795548",
        "Slows everything down to protect the device",
        {},
    ),
]

_COLOR_MAP = {
    "green": 0x07E0,
    "red": 0xF800,
    "blue": 0x001F,
    "yellow": 0xFFE0,
    "white": 0xFFFF,
}

_PITCH_MAP = {"low": 300.0, "medium": 660.0, "high": 1200.0}


def get_brick(brick_id: str) -> BrickSpec | None:
    for brick in BRICK_CATALOG:
        if brick.brick_id == brick_id:
            return brick
    return None


def catalog_for_api() -> list[dict[str, Any]]:
    return [
        {
            "id": b.brick_id,
            "label": b.label,
            "emoji": b.emoji,
            "category": b.category,
            "color": b.color,
            "description": b.description,
            "params": b.params,
        }
        for b in BRICK_CATALOG
    ]


def color_hex(name: str) -> int:
    return _COLOR_MAP.get(name, 0xFFFF)


def pitch_hz(name: str) -> float:
    return _PITCH_MAP.get(name, 660.0)
