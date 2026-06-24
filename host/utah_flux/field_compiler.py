from __future__ import annotations

import re
from typing import Any

from m5resolver.safety import validate_intent_safety
from m5resolver.simulation import HardwareSimulator
from m5resolver.validation import validate_intent_payload

_BINDING_RE = re.compile(
    r"if\s*\(\s*value\s*([<>=!]+)\s*([\d.]+)\s*\)\s*return\s+'([^']+)'\s*;"
    r"\s*else\s*return\s+'([^']+)'\s*;",
    re.I,
)


def is_field_graph_flux(data: dict[str, Any]) -> bool:
    """True for sanctum-style layouts with nodes/bindings (not brick/link projects)."""
    if "bricks" in data or "links" in data:
        return False
    return "nodes" in data or "bindings" in data or (
        isinstance(data.get("layout"), dict) and bool(data["layout"].get("type"))
    )


def rgb888_to_rgb565(rgb: int) -> int:
    r = (rgb >> 16) & 0xFF
    g = (rgb >> 8) & 0xFF
    b = rgb & 0xFF
    return ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)


def parse_hex_color(value: Any, *, default: int = 0xFFFF) -> int:
    if isinstance(value, int):
        return value & 0xFFFF
    text = str(value).strip()
    if text.startswith("#"):
        text = text[1:]
    if len(text) == 6:
        try:
            return rgb888_to_rgb565(int(text, 16))
        except ValueError:
            return default
    return default


def font_size_to_text_size(font_size: Any) -> int:
    try:
        px = int(font_size)
    except (TypeError, ValueError):
        return 2
    return max(1, min(4, px // 8 or 1))


def eval_binding_logic(logic: str, value: float) -> str | None:
    match = _BINDING_RE.match(logic.strip())
    if not match:
        return None
    op, threshold_s, then_val, else_val = match.groups()
    threshold = float(threshold_s)
    if op == "<":
        return then_val if value < threshold else else_val
    if op == "<=":
        return then_val if value <= threshold else else_val
    if op == ">":
        return then_val if value > threshold else else_val
    if op == ">=":
        return then_val if value >= threshold else else_val
    if op == "==":
        return then_val if value == threshold else else_val
    if op == "!=":
        return then_val if value != threshold else else_val
    return None


def movement_delta_from_telemetry(telemetry: dict[str, Any]) -> float:
    accel = telemetry.get("accel")
    if not isinstance(accel, dict):
        return 0.0
    try:
        x = float(accel.get("x", 0.0))
        y = float(accel.get("y", 0.0))
        z = float(accel.get("z", 0.0))
    except (TypeError, ValueError):
        return 0.0
    magnitude = (x * x + y * y + z * z) ** 0.5
    return abs(magnitude - 1.0)


def _node_to_element(node: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    node_id = str(node.get("id", "node"))
    node_type = str(node.get("type", "FieldLabel"))
    props = node.get("properties") or {}
    x = int(props.get("x", 0))
    y = int(props.get("y", 0))

    if node_type == "FieldButton":
        width = int(props.get("width", 80))
        height = int(props.get("height", 40))
        return node_id, {
            "type": "button",
            "x": x,
            "y": y,
            "w": width,
            "h": height,
            "text": str(props.get("text", ""))[:32],
            "color": parse_hex_color(props.get("color", "#FFFFFF")),
            "fill": parse_hex_color(props.get("background_color", "#333333")),
        }

    return node_id, {
        "type": "label",
        "x": x,
        "y": y,
        "text": str(props.get("text", ""))[:48],
        "color": parse_hex_color(props.get("color", "#FFFFFF")),
        "size": font_size_to_text_size(props.get("font_size", 16)),
    }


def _binding_sink_parts(target: str) -> tuple[str, str] | None:
    # voxel_core.properties.background_color -> (voxel_core, fill)
    # status_label.properties.text -> (status_label, text)
    # status_label.properties.color -> (status_label, color)
    parts = target.split(".")
    if len(parts) < 3 or parts[1] != "properties":
        return None
    node_id = parts[0]
    prop = parts[2]
    if prop == "background_color":
        return node_id, "fill"
    if prop in ("text", "color"):
        return node_id, prop
    return None


def _compile_binding_wire(binding: dict[str, Any]) -> dict[str, Any] | None:
    source = str(binding.get("source", ""))
    if source != "sensor.imu.movement_delta":
        return None
    sink_parts = _binding_sink_parts(str(binding.get("target", "")))
    if sink_parts is None:
        return None
    node_id, prop = sink_parts
    logic = str(binding.get("logic", ""))
    value_type = "color" if prop == "fill" or prop == "color" else "string"
    return {
        "source": "movement_delta",
        "sink": ("display", "elements", node_id, prop),
        "transform": "binding_logic",
        "params": {"logic": logic, "value_type": value_type},
    }


def compile_field_graph(project: dict[str, Any]) -> dict[str, Any]:
    """Compile nodes/bindings field graphs into device intent + reactive wires."""
    layout = project.get("layout") or {}
    bg = parse_hex_color(layout.get("background_color", "#000000"), default=0x0000)

    nodes = project.get("nodes") or []
    elements: dict[str, Any] = {}
    for node in nodes:
        if not isinstance(node, dict):
            continue
        node_id, element = _node_to_element(node)
        elements[node_id] = element

    intent: dict[str, Any] = {
        "display": {
            "clear": True,
            "bg_color": bg,
            "elements": elements,
        }
    }

    wires: list[dict[str, Any]] = []
    for binding in project.get("bindings") or []:
        if not isinstance(binding, dict):
            continue
        wire = _compile_binding_wire(binding)
        if wire:
            wires.append(wire)

    # Bindings are evaluated on the host (Ghost Forge wires); no firmware registry unit.

    errors = (
        validate_intent_payload(intent)
        + validate_intent_safety(intent)
        + HardwareSimulator().simulate_intent(intent)
    )

    return {
        "ok": not errors,
        "errors": errors,
        "intent": intent,
        "wires": wires,
        "project_name": project.get("project_name") or project.get("name") or "Field Graph",
    }
