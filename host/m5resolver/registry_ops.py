from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .registry import DriverRegistry
from .safety import validate_registry_safety
from .simulation import HardwareSimulator


class RegistryStore:
    """Read/write registry with staged validation (SIL gate)."""

    def __init__(self, registry_file: str | Path) -> None:
        self.registry_file = Path(registry_file)
        self.simulator = HardwareSimulator()

    def load_raw(self) -> dict[str, Any]:
        return json.loads(self.registry_file.read_text(encoding="utf-8"))

    def save_raw(self, payload: dict[str, Any], *, simulate: bool = True) -> list[str]:
        if simulate:
            sim_errors = self.simulator.simulate_registry_patch(payload)
            if sim_errors:
                return sim_errors
        safety_errors = validate_registry_safety(payload)
        if safety_errors:
            return safety_errors
        self.registry_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return []

    def merge_runtime_units(self, runtime_units: dict[str, Any]) -> list[str]:
        raw = self.load_raw()
        units = raw.setdefault("units", [])
        if isinstance(units, list):
            by_id = {u.get("unit_id"): u for u in units if isinstance(u, dict) and "unit_id" in u}
            for unit_id, cfg in runtime_units.items():
                record = {"unit_id": unit_id, **cfg}
                by_id[unit_id] = record
            raw["units"] = list(by_id.values())
        elif isinstance(units, dict):
            units.update(runtime_units)
        else:
            raw["units"] = runtime_units
        return self.save_raw(raw)

    def to_driver_registry(self) -> DriverRegistry:
        reg = DriverRegistry(self.registry_file)
        reg.load()
        return reg

    def list_bounty_units(self) -> list[dict[str, Any]]:
        raw = self.load_raw()
        units = raw.get("units", [])
        if isinstance(units, dict):
            iterable = units.values()
        else:
            iterable = units
        return [u for u in iterable if isinstance(u, dict) and u.get("bounty_id")]
