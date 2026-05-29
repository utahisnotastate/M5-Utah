from __future__ import annotations

from typing import Any

from .safety import MAX_ESTIMATED_POWER_MA, validate_intent_safety, validate_registry_safety


class HardwareSimulator:
    """Simulation-in-the-loop gate before pushing registry/intent updates."""

    def __init__(self, max_power_ma: int = MAX_ESTIMATED_POWER_MA) -> None:
        self.max_power_ma = max_power_ma

    def simulate_intent(self, intent: dict[str, Any]) -> list[str]:
        errors = validate_intent_safety(intent)
        if errors:
            return errors

        power_draw = self.estimate_power_draw(intent)
        if power_draw > self.max_power_ma:
            return [f"simulated power draw {power_draw}mA exceeds limit {self.max_power_ma}mA"]
        return []

    def simulate_registry_patch(self, registry: dict[str, Any]) -> list[str]:
        errors = validate_registry_safety(registry)
        if errors:
            return errors
        power_draw = self._estimate_registry_power(registry)
        if power_draw > self.max_power_ma:
            return [f"simulated registry power {power_draw}mA exceeds limit {self.max_power_ma}mA"]
        return []

    def estimate_power_draw(self, intent: dict[str, Any]) -> int:
        draw = 50  # base MCU draw estimate (mA)
        speaker = intent.get("speaker")
        if isinstance(speaker, dict) and "tone" in speaker:
            draw += 80
        display = intent.get("display")
        if isinstance(display, dict):
            draw += 40
        registry = intent.get("registry")
        if isinstance(registry, dict):
            draw += self._estimate_registry_power(registry)
        return draw

    def _estimate_registry_power(self, registry: dict[str, Any]) -> int:
        units = registry.get("units", {})
        count = len(units) if isinstance(units, dict) else len(units) if isinstance(units, list) else 0
        return 30 + (count * 25)
