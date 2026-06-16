"""Tests for Immortal Bootloader host-side hardware matrix."""

import json

from utah_flux.hardware_matrix import (
    I2C_ADDRESS_UNITS,
    HardwareMatrix,
    is_utah_core_port,
    load_registry_address_map,
    parse_discovery_line,
)


class FakePort:
    def __init__(self, device: str, hwid: str = "", description: str = "", manufacturer: str = ""):
        self.device = device
        self.hwid = hwid
        self.description = description
        self.manufacturer = manufacturer


def test_is_utah_core_port_detects_espressif_vid():
    port = FakePort("COM7", hwid="USB VID:PID=303A:1001")
    assert is_utah_core_port(port) is True


def test_is_utah_core_port_detects_esp32_description():
    port = FakePort("COM3", description="USB Serial Device (ESP32-S3)")
    assert is_utah_core_port(port) is True


def test_parse_discovery_line_enriches_from_registry(tmp_path):
    registry = tmp_path / "units.json"
    registry.write_text(
        json.dumps(
            {
                "units": [
                    {"unit_id": "env4", "bus": "i2c", "address": 68},
                ]
            }
        ),
        encoding="utf-8",
    )
    mapping = load_registry_address_map(registry)
    line = '{"event":"discovery","port":"A","hex_address":68,"unit":"UNKNOWN_SILICON"}'
    payload = parse_discovery_line(line, mapping)
    assert payload is not None
    assert payload["unit"] == "env4"


def test_hardware_matrix_tracks_connect_disconnect():
    matrix = HardwareMatrix()
    matrix.ingest_line(
        '{"event":"discovery","port":"A","hex_address":68,"unit":"MPU6886_IMU"}'
    )
    assert len(matrix.connected_units) == 1
    matrix.ingest_line('{"event":"disconnect","port":"A","hex_address":68}')
    assert matrix.connected_units == []


def test_i2c_address_units_contains_env_iii():
    assert I2C_ADDRESS_UNITS[0x44] == "ENV_III_SENSOR"
