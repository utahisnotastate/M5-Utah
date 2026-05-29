from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from .registry_ops import RegistryStore
from .simulation import HardwareSimulator
from .validation import validate_intent_payload
from .safety import validate_intent_safety

logger = logging.getLogger("m5resolver.agent")


@dataclass
class DeviceState:
    """In-memory device state held by the observability agent."""

    last_telemetry: dict[str, Any] = field(default_factory=dict)
    history: list[dict[str, Any]] = field(default_factory=list)
    anomaly_count: int = 0
    safeguard_active: bool = False

    def update(self, telemetry: dict[str, Any]) -> None:
        self.last_telemetry = telemetry
        self.history.append(telemetry)
        if len(self.history) > 200:
            self.history = self.history[-200:]


class AgenticController:
    """
    Active Registry Observer: monitors telemetry, validates contracts,
    and synthesizes corrective intents/registry patches.
    """

    def __init__(
        self,
        registry_path: str | Path,
        telemetry_schema_path: str | Path | None = None,
        on_corrective_intent: Callable[[dict[str, Any]], None] | None = None,
    ) -> None:
        self.registry_store = RegistryStore(registry_path)
        self.simulator = HardwareSimulator()
        self.state = DeviceState()
        self.on_corrective_intent = on_corrective_intent
        self.telemetry_schema: dict[str, Any] = {}
        if telemetry_schema_path:
            self.telemetry_schema = json.loads(Path(telemetry_schema_path).read_text(encoding="utf-8"))

    def ingest_telemetry(self, telemetry: dict[str, Any]) -> dict[str, Any] | None:
        self.state.update(telemetry)
        anomalies = self._detect_anomalies(telemetry)
        if not anomalies:
            return None

        self.state.anomaly_count += 1
        logger.warning("Telemetry anomalies detected: %s", anomalies)
        return self.execute_autonomous_remediation(anomalies)

    def observe_and_correct(self, telemetry: dict[str, Any]) -> dict[str, Any] | None:
        """Reactive registry adjustment based on live telemetry."""
        temp = telemetry.get("temperature_c") or telemetry.get("temp")
        if isinstance(temp, (int, float)) and temp > 80:
            patch = {
                "units": {
                    "thermal_mgt": {
                        "unit_id": "thermal_mgt",
                        "state": "throttled",
                        "priority": 1,
                        "frequency_hz": 1,
                        "max_power_ma": 30,
                        "semantic_action": "ACTION_INDICATE_ALERT",
                    }
                }
            }
            errors = self.registry_store.save_raw(
                self._merge_registry_patch(patch),
                simulate=True,
            )
            if errors:
                logger.error("Thermal registry patch rejected: %s", errors)
                return None
            self.state.safeguard_active = True
            return {"registry": patch, "display": {"text": {"payload": "THERMAL SAFE", "x": 8, "y": 40, "size": 2, "color": 0xF800}}}

        return self.ingest_telemetry(telemetry)

    def execute_autonomous_remediation(self, trigger_causes: list[str]) -> dict[str, Any]:
        logger.info("Initiating remediation for: %s", trigger_causes)
        raw = self.registry_store.load_raw()
        units = raw.get("units", [])
        if isinstance(units, list):
            for unit in units:
                if isinstance(unit, dict) and "frequency_hz" in unit:
                    unit["frequency_hz"] = 1
                    unit["safeguard_activated"] = True
        elif isinstance(units, dict):
            for unit in units.values():
                if isinstance(unit, dict) and "frequency_hz" in unit:
                    unit["frequency_hz"] = 1
                    unit["safeguard_activated"] = True

        self.registry_store.save_raw(raw, simulate=True)
        self.state.safeguard_active = True

        corrective = {
            "speaker": {"stop": True},
            "power": {"led": 8},
            "display": {
                "clear": True,
                "text": {
                    "x": 8,
                    "y": 24,
                    "size": 2,
                    "color": 0xF800,
                    "payload": "SAFE MODE",
                },
            },
            "registry": {"safeguard": True, "units": units if isinstance(units, dict) else {}},
        }
        errors = validate_intent_payload(corrective) + validate_intent_safety(corrective)
        if errors:
            logger.error("Corrective intent failed validation: %s", errors)
            corrective = {"speaker": {"stop": True}}

        sim_errors = self.simulator.simulate_intent(corrective)
        if sim_errors:
            logger.error("Corrective intent failed simulation: %s", sim_errors)
            corrective = {"speaker": {"stop": True}}

        if self.on_corrective_intent:
            self.on_corrective_intent(corrective)
        return corrective

    def stage_intent(self, intent: dict[str, Any]) -> list[str]:
        """Staggered deployment: validate + simulate before hardware push."""
        errors = validate_intent_payload(intent) + validate_intent_safety(intent)
        if errors:
            return errors
        return self.simulator.simulate_intent(intent)

    def _detect_anomalies(self, telemetry: dict[str, Any]) -> list[str]:
        causes: list[str] = []
        status = telemetry.get("status")
        if status == "error":
            causes.append("status_error")

        metrics = telemetry.get("metrics", {})
        if isinstance(metrics, dict):
            heap = metrics.get("free_heap")
            if isinstance(heap, int) and heap < 30000:
                causes.append("low_heap")

        if telemetry.get("type") == "telemetry":
            battery = telemetry.get("battery_pct")
            if isinstance(battery, int) and battery < 5:
                causes.append("critical_battery")

        return causes

    def _merge_registry_patch(self, patch: dict[str, Any]) -> dict[str, Any]:
        raw = self.registry_store.load_raw()
        units = raw.get("units", [])
        runtime = patch.get("units", {})
        if isinstance(units, list) and isinstance(runtime, dict):
            by_id = {u.get("unit_id"): u for u in units if isinstance(u, dict) and "unit_id" in u}
            by_id.update(runtime)
            raw["units"] = list(by_id.values())
        elif isinstance(units, dict) and isinstance(runtime, dict):
            units.update(runtime)
        else:
            raw["units"] = runtime
        return raw
