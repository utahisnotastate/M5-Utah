import json
from pathlib import Path

from utah_flux.compiler import compile_flux_document
from utah_flux.field_compiler import (
    eval_binding_logic,
    is_field_graph_flux,
    movement_delta_from_telemetry,
)


SANCTUM = {
    "project_name": "Sanctum_Voxel_Alpha",
    "target_hardware": "CoreS3",
    "intent": "Stabilize local kinetic energy into visual coherence.",
    "layout": {"type": "GravitationalField", "background_color": "#000000"},
    "nodes": [
        {
            "id": "status_label",
            "type": "FieldLabel",
            "properties": {
                "text": "AWAITING COHERENCE...",
                "color": "#FF0000",
                "font_size": 24,
                "x": 160,
                "y": 60,
            },
        },
        {
            "id": "voxel_core",
            "type": "FieldButton",
            "properties": {
                "text": "CHAOS",
                "color": "#FFFFFF",
                "background_color": "#333333",
                "width": 100,
                "height": 100,
                "x": 160,
                "y": 160,
            },
        },
    ],
    "bindings": [
        {
            "source": "sensor.imu.movement_delta",
            "target": "voxel_core.properties.background_color",
            "logic": "if (value < 0.05) return '#FFD700'; else return '#333333';",
        },
        {
            "source": "sensor.imu.movement_delta",
            "target": "status_label.properties.text",
            "logic": "if (value < 0.05) return 'TIMELINE STABILIZED'; else return 'KINETIC INTERFERENCE DETECTED';",
        },
    ],
}


def test_is_field_graph_flux():
    assert is_field_graph_flux(SANCTUM) is True
    assert is_field_graph_flux({"name": "x", "version": 1, "bricks": []}) is False


def test_compile_sanctum_field_graph():
    result = compile_flux_document(SANCTUM)
    assert result["ok"] is True
    display = result["intent"]["display"]
    assert display["bg_color"] == 0
    assert "status_label" in display["elements"]
    assert display["elements"]["voxel_core"]["type"] == "button"
    assert len(result["wires"]) == 2
    assert "registry" not in result["intent"]


def test_binding_logic_and_movement_delta():
    logic = "if (value < 0.05) return 'STABLE'; else return 'CHAOS';"
    assert eval_binding_logic(logic, 0.01) == "STABLE"
    assert eval_binding_logic(logic, 0.5) == "CHAOS"
    delta = movement_delta_from_telemetry({"accel": {"x": 0.0, "y": 0.0, "z": 1.1}})
    assert delta > 0.05


def test_parse_hex_color_rgb565():
    from utah_flux.field_compiler import parse_hex_color

    assert parse_hex_color("#FF0000") == 0xF800
    assert parse_hex_color("#00FF00") == 0x07E0
    assert parse_hex_color("#FFFFFF") == 0xFFFF
    assert parse_hex_color("#333333") == 0x3186


def test_sanctum_example_file_if_present():
    path = Path(__file__).resolve().parents[1] / "projects" / "sanctum.flux.json"
    if not path.is_file():
        return
    result = compile_flux_document(json.loads(path.read_text(encoding="utf-8")))
    assert result["ok"] is True
