from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class UnitSpec:
    unit_id: str
    bus: str
    address: int | None
    capabilities: list[str]
    register_map: dict[str, Any]
    bounty_id: str | None = None
    semantic_action: str | None = None
    frequency_hz: int | None = None
    max_power_ma: int | None = None


class DriverRegistry:
    """JSON-backed registry for dynamic unit definitions."""

    def __init__(self, registry_file: str | Path) -> None:
        self.registry_file = Path(registry_file)
        self._units: dict[str, UnitSpec] = {}

    def load(self) -> None:
        raw = json.loads(self.registry_file.read_text(encoding="utf-8"))
        units: dict[str, UnitSpec] = {}
        for record in raw.get("units", []):
            spec = UnitSpec(
                unit_id=record["unit_id"],
                bus=record["bus"],
                address=record.get("address"),
                capabilities=list(record.get("capabilities", [])),
                register_map=dict(record.get("register_map", {})),
                bounty_id=record.get("bounty_id"),
                semantic_action=record.get("semantic_action"),
                frequency_hz=record.get("frequency_hz"),
                max_power_ma=record.get("max_power_ma"),
            )
            units[spec.unit_id] = spec
        self._units = units

    def get(self, unit_id: str) -> UnitSpec | None:
        return self._units.get(unit_id)

    def list_ids(self) -> list[str]:
        return sorted(self._units.keys())
