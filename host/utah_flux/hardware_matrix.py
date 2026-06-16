from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger("utah_flux.hardware_matrix")

ESPRESSIF_USB_VID = "303A"
DEFAULT_BAUD = 115200

# Well-known I2C silicon (mirrors firmware ImmortalDiscovery lookup).
I2C_ADDRESS_UNITS: dict[int, str] = {
    0x44: "ENV_III_SENSOR",
    0x70: "ENV_III_SENSOR",
    0x68: "MPU6886_IMU",
    0x41: "VL53L1X_TOF",
    0x76: "BMP280_ENV",
    0x77: "BMP280_ENV",
}


def load_registry_address_map(registry_path: str | Path | None = None) -> dict[int, str]:
    """Merge registry/units.json I2C addresses into the discovery lookup table."""
    mapping = dict(I2C_ADDRESS_UNITS)
    path = Path(registry_path or "registry/units.json")
    if not path.is_file():
        return mapping
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        logger.warning("registry load failed: %s", exc)
        return mapping

    units = data.get("units", [])
    if isinstance(units, list):
        for unit in units:
            if not isinstance(unit, dict):
                continue
            if unit.get("bus") != "i2c":
                continue
            address = unit.get("address")
            unit_id = unit.get("unit_id")
            if isinstance(address, int) and isinstance(unit_id, str):
                mapping[address] = unit_id
    return mapping


def is_utah_core_port(port: Any) -> bool:
    """True when a COM port looks like an Espressif M5Stack / ESP32-S3 USB serial device."""
    hwid = str(getattr(port, "hwid", "") or "").upper()
    description = str(getattr(port, "description", "") or "").upper()
    manufacturer = str(getattr(port, "manufacturer", "") or "").upper()
    if ESPRESSIF_USB_VID in hwid:
        return True
    if "ESP32" in description or "ESP32" in manufacturer:
        return True
    if "M5STACK" in description or "M5STACK" in manufacturer:
        return True
    if "USB JTAG" in description and "SERIAL" in description:
        return True
    return False


def scan_for_utah_core() -> str | None:
    """
    Bypass manual COM port selection — scan USB for Espressif CoreS3 serial.
    """
    try:
        import serial.tools.list_ports
    except ImportError:
        logger.error("pyserial not installed")
        return None

    for port in serial.tools.list_ports.comports():
        if is_utah_core_port(port):
            device = getattr(port, "device", None)
            if device:
                logger.info("[UTAH-1] Hardware matrix locked on %s", device)
                return str(device)
    return None


def parse_discovery_line(line: str, registry_map: dict[int, str] | None = None) -> dict[str, Any] | None:
    """Parse JSON discovery/disconnect telemetry from the Immortal Bootloader."""
    text = line.strip()
    if not text.startswith("{"):
        return None
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return None
    if payload.get("event") not in ("discovery", "disconnect"):
        return None

    address = payload.get("hex_address")
    if isinstance(address, int) and registry_map:
        unit = registry_map.get(address)
        if unit:
            payload["unit"] = unit
    return payload


class HardwareMatrix:
    """Shared serial bridge for Omniscient OS and UtahClaw daemons."""

    def __init__(self, *, baud: int = DEFAULT_BAUD, registry_path: str | Path | None = None) -> None:
        self.baud = baud
        self.registry_path = registry_path
        self.active_port: str | None = None
        self.serial_conn: Any = None
        self.connected_units: list[dict[str, Any]] = []
        self._registry_map = load_registry_address_map(registry_path)

    def refresh_registry(self) -> None:
        self._registry_map = load_registry_address_map(self.registry_path)

    def scan_for_utah_core(self) -> str | None:
        return scan_for_utah_core()

    def connect(self, port: str | None = None) -> bool:
        import serial

        target = port or scan_for_utah_core()
        if not target:
            return False
        try:
            if self.serial_conn and getattr(self.serial_conn, "is_open", False):
                self.serial_conn.close()
            self.serial_conn = serial.Serial(target, self.baud, timeout=0.1)
            self.active_port = target
            return True
        except OSError as exc:
            logger.error("linkage failure on %s: %s", target, exc)
            self.serial_conn = None
            self.active_port = None
            return False

    def disconnect(self) -> None:
        if self.serial_conn and getattr(self.serial_conn, "is_open", False):
            self.serial_conn.close()
        self.serial_conn = None
        self.active_port = None

    def readline_text(self) -> str | None:
        if not self.serial_conn or not getattr(self.serial_conn, "is_open", False):
            return None
        if self.serial_conn.in_waiting <= 0:
            return None
        raw = self.serial_conn.readline()
        if not raw:
            return None
        return raw.decode("utf-8", errors="replace").strip()

    def ingest_line(self, line: str) -> dict[str, Any] | None:
        payload = parse_discovery_line(line, self._registry_map)
        if payload is None:
            return None
        if payload.get("event") == "discovery":
            self.connected_units = [u for u in self.connected_units if u.get("hex_address") != payload.get("hex_address")]
            self.connected_units.append(payload)
        elif payload.get("event") == "disconnect":
            address = payload.get("hex_address")
            self.connected_units = [u for u in self.connected_units if u.get("hex_address") != address]
        return payload

    def push_intent_json(self, intent: dict[str, Any]) -> None:
        if not self.serial_conn or not getattr(self.serial_conn, "is_open", False):
            raise RuntimeError("serial link is not open")
        payload = json.dumps(intent, separators=(",", ":")) + "\n"
        self.serial_conn.write(payload.encode("utf-8"))
        self.serial_conn.flush()

    def push_code_paste_mode(self, code_string: str) -> None:
        """MicroPython REPL paste mode injection (CTRL-E / CTRL-D)."""
        if not self.serial_conn or not getattr(self.serial_conn, "is_open", False):
            raise RuntimeError("serial link is not open")
        self.serial_conn.write(b"\x05")
        self.serial_conn.write(code_string.encode("utf-8"))
        self.serial_conn.write(b"\x04")
        self.serial_conn.flush()
