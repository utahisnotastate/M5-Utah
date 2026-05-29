from __future__ import annotations

from typing import Any

from m5resolver.safety import validate_intent_safety
from m5resolver.simulation import HardwareSimulator
from m5resolver.validation import validate_intent_payload

from .bricks import color_hex, pitch_hz
from .project import FluxProject


def _merge_intent(base: dict[str, Any], patch: dict[str, Any]) -> dict[str, Any]:
    for key, value in patch.items():
        if key not in base:
            base[key] = value
            continue
        if isinstance(base[key], dict) and isinstance(value, dict):
            _merge_intent(base[key], value)
        else:
            base[key] = value
    return base


def _compile_action_brick(brick_type: str, params: dict[str, Any]) -> dict[str, Any]:
    if brick_type == "show_message":
        return {
            "display": {
                "clear": True,
                "text": {
                    "x": 8,
                    "y": 40,
                    "size": 2,
                    "color": color_hex(str(params.get("color", "green"))),
                    "payload": str(params.get("text", "Hello!"))[:48],
                },
            }
        }
    if brick_type == "play_sound":
        pitch = pitch_hz(str(params.get("pitch", "medium")))
        duration = 200 if params.get("length") == "long" else 80
        return {"speaker": {"tone": {"frequency": pitch, "duration": duration, "channel": 0}}}
    if brick_type == "happy_blink":
        return {
            "display": {
                "clear": True,
                "text": {"x": 8, "y": 40, "size": 2, "color": color_hex("green"), "payload": "YAY!"},
            },
            "speaker": {"tone": {"frequency": 880.0, "duration": 60, "channel": 0}},
            "registry": {
                "units": {
                    "happy_unit": {
                        "semantic_action": "ACTION_INDICATE_STATUS_SUCCESS",
                        "frequency_hz": 2,
                        "priority": 1,
                    }
                }
            },
        }
    if brick_type == "alert_alarm":
        return {
            "display": {
                "clear": True,
                "text": {"x": 8, "y": 40, "size": 2, "color": color_hex("red"), "payload": "ALERT!"},
            },
            "speaker": {"tone": {"frequency": 1200.0, "duration": 150, "channel": 0}},
            "registry": {
                "units": {
                    "alert_unit": {
                        "semantic_action": "ACTION_INDICATE_ALERT",
                        "frequency_hz": 4,
                        "priority": 2,
                    }
                }
            },
        }
    if brick_type == "clear_screen":
        return {"display": {"clear": True, "bg_color": 0}}
    if brick_type == "party_mode":
        return {
            "display": {
                "clear": True,
                "text": {"x": 8, "y": 40, "size": 3, "color": color_hex("yellow"), "payload": "PARTY!"},
            },
            "speaker": {"tone": {"frequency": 990.0, "duration": 120, "channel": 0}},
        }
    if brick_type == "read_motion":
        return {
            "display": {"text": {"x": 8, "y": 60, "size": 2, "color": color_hex("blue"), "payload": "Motion..."}},
            "registry": {
                "units": {
                    "motion_reader": {
                        "semantic_action": "ACTION_REACT_TO_MOTION",
                        "frequency_hz": 10,
                        "priority": 2,
                    }
                }
            },
        }
    if brick_type == "safe_mode":
        return {
            "registry": {"safeguard": True, "units": {}},
            "speaker": {"stop": True},
            "power": {"led": 4},
        }
    return {}


def compile_project(project: FluxProject | dict[str, Any]) -> dict[str, Any]:
    """Compile Lego bricks + links into intents, wires, and registry patches."""
    if isinstance(project, dict):
        project = FluxProject.from_dict(project)

    by_id = {b["id"]: b for b in project.bricks}
    intent: dict[str, Any] = {}
    wires: list[dict[str, Any]] = []
    registry_units: dict[str, Any] = {}

    triggers = {b["id"] for b in project.bricks if _is_trigger(b.get("type", ""))}
    linked_actions: dict[str, list[str]] = {tid: [] for tid in triggers}

    for link in project.links:
        src = link.get("from", "")
        dst = link.get("to", "")
        if src in triggers and dst in by_id:
            linked_actions.setdefault(src, []).append(dst)

    for brick in project.bricks:
        brick_type = brick.get("type", "")
        params = brick.get("params", {})
        if brick_type == "when_start":
            for action_id in linked_actions.get(brick["id"], []):
                action = by_id.get(action_id)
                if action:
                    _merge_intent(intent, _compile_action_brick(action["type"], action.get("params", {})))
        elif brick_type in ("when_tilt", "when_loud") and not linked_actions.get(brick["id"]):
            pass

    for trigger_id, action_ids in linked_actions.items():
        trigger = by_id.get(trigger_id)
        if not trigger:
            continue
        trigger_type = trigger.get("type", "")
        source_key = "accel.x" if trigger_type == "when_tilt" else "accel.z"

        for action_id in action_ids:
            action = by_id.get(action_id)
            if not action:
                continue
            action_type = action.get("type", "")
            params = action.get("params", {})

            if action_type == "show_message":
                wires.append(
                    {
                        "source": source_key,
                        "sink": ("display", "text", "payload"),
                        "transform": "tilt_message",
                        "params": params,
                    }
                )
                wires.append(
                    {
                        "source": source_key,
                        "sink": ("display", "clear"),
                        "transform": "const_true",
                    }
                )
            elif action_type == "play_sound":
                wires.append(
                    {
                        "source": source_key,
                        "sink": ("speaker", "tone", "frequency"),
                        "transform": "tilt_pitch",
                        "params": params,
                    }
                )
                wires.append(
                    {
                        "source": source_key,
                        "sink": ("speaker", "tone", "duration"),
                        "transform": "const_duration",
                        "params": params,
                    }
                )
            else:
                patch = _compile_action_brick(action_type, params)
                reg = patch.get("registry", {}).get("units", {})
                if isinstance(reg, dict):
                    registry_units.update(reg)
                _merge_intent(intent, {k: v for k, v in patch.items() if k != "registry"})

    if registry_units:
        intent.setdefault("registry", {"units": {}})
        intent["registry"]["units"].update(registry_units)

    simulator = HardwareSimulator()
    errors = validate_intent_payload(intent) + validate_intent_safety(intent) + simulator.simulate_intent(intent)

    return {
        "ok": not errors,
        "errors": errors,
        "intent": intent,
        "wires": wires,
        "project_name": project.name,
    }


def _is_trigger(brick_type: str) -> bool:
    return brick_type.startswith("when_")


def apply_wire_transform(transform: str, value: Any, params: dict[str, Any]) -> Any:
    if transform == "const_true":
        return True
    if transform == "const_duration":
        return 200 if params.get("length") == "long" else 80
    if transform == "tilt_message":
        text = str(params.get("text", "Tilt!"))
        return f"{text} ({float(value):.2f})"
    if transform == "tilt_pitch":
        base = pitch_hz(str(params.get("pitch", "medium")))
        return min(1800.0, max(220.0, base + abs(float(value)) * 200.0))
    return value
