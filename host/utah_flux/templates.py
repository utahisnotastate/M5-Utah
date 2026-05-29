from __future__ import annotations

from typing import Any

STARTER_TEMPLATES: list[dict[str, Any]] = [
    {
        "id": "hello",
        "name": "Hello Screen",
        "emoji": "👋",
        "description": "Shows a friendly message when you press Play",
        "project": {
            "version": 1,
            "name": "Hello Screen",
            "bricks": [
                {"id": "t1", "type": "when_start", "x": 80, "y": 80, "params": {}},
                {
                    "id": "a1",
                    "type": "show_message",
                    "x": 80,
                    "y": 220,
                    "params": {"text": "Hello!", "color": "green"},
                },
            ],
            "links": [{"from": "t1", "to": "a1"}],
        },
    },
    {
        "id": "tilt_alarm",
        "name": "Tilt Alarm",
        "emoji": "📐",
        "description": "Beeps and shows text when you tilt the device",
        "project": {
            "version": 1,
            "name": "Tilt Alarm",
            "bricks": [
                {"id": "t1", "type": "when_tilt", "x": 60, "y": 60, "params": {"sensitivity": 0.3}},
                {
                    "id": "a1",
                    "type": "show_message",
                    "x": 60,
                    "y": 200,
                    "params": {"text": "Tilting!", "color": "yellow"},
                },
                {
                    "id": "a2",
                    "type": "play_sound",
                    "x": 280,
                    "y": 200,
                    "params": {"pitch": "high", "length": "short"},
                },
            ],
            "links": [{"from": "t1", "to": "a1"}, {"from": "t1", "to": "a2"}],
        },
    },
    {
        "id": "party",
        "name": "Party Mode",
        "emoji": "🎉",
        "description": "A fun party screen and sound",
        "project": {
            "version": 1,
            "name": "Party Mode",
            "bricks": [
                {"id": "t1", "type": "when_start", "x": 100, "y": 80, "params": {}},
                {"id": "a1", "type": "party_mode", "x": 100, "y": 220, "params": {}},
            ],
            "links": [{"from": "t1", "to": "a1"}],
        },
    },
    {
        "id": "motion_dashboard",
        "name": "Motion Dashboard",
        "emoji": "📡",
        "description": "Live motion reading on screen",
        "project": {
            "version": 1,
            "name": "Motion Dashboard",
            "bricks": [
                {"id": "t1", "type": "when_tilt", "x": 80, "y": 80, "params": {}},
                {"id": "a1", "type": "read_motion", "x": 80, "y": 220, "params": {}},
                {"id": "a2", "type": "play_sound", "x": 300, "y": 220, "params": {"pitch": "low", "length": "short"}},
            ],
            "links": [{"from": "t1", "to": "a1"}, {"from": "t1", "to": "a2"}],
        },
    },
]


def list_templates() -> list[dict[str, Any]]:
    return [
        {
            "id": t["id"],
            "name": t["name"],
            "emoji": t["emoji"],
            "description": t["description"],
        }
        for t in STARTER_TEMPLATES
    ]


def get_template(template_id: str) -> dict[str, Any] | None:
    for t in STARTER_TEMPLATES:
        if t["id"] == template_id:
            return t["project"]
    return None
