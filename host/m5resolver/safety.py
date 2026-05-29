from __future__ import annotations

from typing import Any

# Hardware safety envelope (Hardware Context Protocol defaults)
MAX_SPEAKER_FREQUENCY_HZ = 4000.0
MIN_SPEAKER_FREQUENCY_HZ = 20.0
MAX_TONE_DURATION_MS = 5000
MAX_LED_BRIGHTNESS = 255
MAX_UNIT_FREQUENCY_HZ = 60
MAX_I2C_BUS_FREQUENCY_HZ = 1_000_000
MAX_REGISTRY_UNITS = 10
MAX_ESTIMATED_POWER_MA = 500
MIN_FREE_HEAP_BYTES = 20000


def validate_intent_safety(intent: dict[str, Any]) -> list[str]:
    errors: list[str] = []

    speaker = intent.get("speaker")
    if isinstance(speaker, dict):
        tone = speaker.get("tone")
        if isinstance(tone, dict):
            freq = tone.get("frequency")
            if isinstance(freq, (int, float)):
                if freq < MIN_SPEAKER_FREQUENCY_HZ or freq > MAX_SPEAKER_FREQUENCY_HZ:
                    errors.append(
                        f"speaker.tone.frequency out of safe range "
                        f"({MIN_SPEAKER_FREQUENCY_HZ}-{MAX_SPEAKER_FREQUENCY_HZ} Hz)"
                    )
            duration = tone.get("duration")
            if isinstance(duration, int) and duration > MAX_TONE_DURATION_MS:
                errors.append(f"speaker.tone.duration exceeds {MAX_TONE_DURATION_MS}ms")

    power = intent.get("power")
    if isinstance(power, dict):
        led = power.get("led")
        if isinstance(led, int) and (led < 0 or led > MAX_LED_BRIGHTNESS):
            errors.append(f"power.led must be 0-{MAX_LED_BRIGHTNESS}")

    registry = intent.get("registry")
    if isinstance(registry, dict):
        errors.extend(validate_registry_safety(registry))

    return errors


def validate_registry_safety(registry: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    units = registry.get("units")
    if units is None:
        return errors
    if isinstance(units, list):
        if len(units) > MAX_REGISTRY_UNITS:
            errors.append(f"registry exceeds max units ({MAX_REGISTRY_UNITS})")
        for unit in units:
            if isinstance(unit, dict):
                errors.extend(_validate_unit_record(unit))
    elif isinstance(units, dict):
        if len(units) > MAX_REGISTRY_UNITS:
            errors.append(f"registry exceeds max units ({MAX_REGISTRY_UNITS})")
        for unit in units.values():
            if isinstance(unit, dict):
                errors.extend(_validate_unit_record(unit))
    else:
        errors.append("registry.units must be array or object")
    return errors


def _validate_unit_record(unit: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    freq = unit.get("frequency_hz")
    unit_type = str(unit.get("type", "")).upper()
    if isinstance(freq, (int, float)):
        if unit_type in ("I2C", "SPI"):
            if freq > MAX_I2C_BUS_FREQUENCY_HZ:
                errors.append(
                    f"unit bus frequency_hz exceeds safe limit ({MAX_I2C_BUS_FREQUENCY_HZ})"
                )
        elif freq > MAX_UNIT_FREQUENCY_HZ:
            errors.append(f"unit frequency_hz exceeds safe limit ({MAX_UNIT_FREQUENCY_HZ})")
    power = unit.get("max_power_ma")
    if isinstance(power, (int, float)) and power > MAX_ESTIMATED_POWER_MA:
        errors.append(f"unit max_power_ma exceeds platform limit ({MAX_ESTIMATED_POWER_MA}mA)")
    priority = unit.get("priority")
    if isinstance(priority, int) and priority < 0:
        errors.append("unit priority must be >= 0")
    return errors
