from __future__ import annotations

from typing import Any

MAX_I2C_FREQUENCY_HZ = 1_000_000
MIN_I2C_FREQUENCY_HZ = 10_000
VALID_BUS_TYPES = {"raw_gpio", "gpio", "I2C", "i2c", "SPI", "spi", "PWM", "pwm"}


def validate_bus_multiplexing(registry: dict[str, Any]) -> list[str]:
    """Validate dynamic hardware protocol maps in registry units."""
    errors: list[str] = []
    units = registry.get("units")
    if units is None:
        return errors

    iterable: list[tuple[str, dict[str, Any]]] = []
    if isinstance(units, dict):
        iterable = [(k, v) for k, v in units.items() if isinstance(v, dict)]
    elif isinstance(units, list):
        for unit in units:
            if isinstance(unit, dict):
                uid = str(unit.get("unit_id", "unit"))
                iterable.append((uid, unit))

    claimed_pins: dict[int, str] = {}

    for unit_id, unit in iterable:
        errors.extend(_validate_unit_bus(unit_id, unit, claimed_pins))

    return errors


def _validate_unit_bus(unit_id: str, unit: dict[str, Any], claimed_pins: dict[int, str]) -> list[str]:
    errors: list[str] = []
    bus_type = unit.get("type") or unit.get("bus_type") or unit.get("bus")
    if bus_type is None:
        return errors

    normalized = str(bus_type)
    if normalized not in VALID_BUS_TYPES and normalized not in {"internal"}:
        errors.append(f"unit {unit_id}: unsupported bus type {normalized}")

    pins = _extract_pins(unit)

    if normalized.lower() == "i2c":
        if len(pins) < 2:
            errors.append(f"unit {unit_id}: I2C requires two pins [SDA, SCL]")
        elif pins[0] == pins[1]:
            errors.append(f"Pin conflict: unit {unit_id} uses identical pin {pins[0]} for SDA and SCL")
        freq = unit.get("frequency_hz") or unit.get("i2c_frequency") or 100_000
        if isinstance(freq, (int, float)):
            if freq < MIN_I2C_FREQUENCY_HZ or freq > MAX_I2C_FREQUENCY_HZ:
                errors.append(
                    f"unit {unit_id}: I2C frequency {freq} out of range "
                    f"({MIN_I2C_FREQUENCY_HZ}-{MAX_I2C_FREQUENCY_HZ})"
                )

    if normalized.lower() == "spi" and len(pins) < 2:
        errors.append(f"unit {unit_id}: SPI requires at least MOSI and SCLK pins")

    if normalized.lower() == "pwm" and not pins:
        errors.append(f"unit {unit_id}: PWM requires at least one pin")

    for pin in pins:
        if pin in claimed_pins and claimed_pins[pin] != unit_id:
            errors.append(f"Pin conflict: pin {pin} claimed by {claimed_pins[pin]} and {unit_id}")
        elif pin >= 0:
            claimed_pins[pin] = unit_id

    return errors


def _extract_pins(unit: dict[str, Any]) -> list[int]:
    pins_raw = unit.get("pins")
    if isinstance(pins_raw, list):
        return [int(p) for p in pins_raw if isinstance(p, (int, float))]
    result: list[int] = []
    for key in ("sda", "scl", "mosi", "miso", "sclk", "cs"):
        if key in unit and isinstance(unit[key], (int, float)):
            result.append(int(unit[key]))
    return result
