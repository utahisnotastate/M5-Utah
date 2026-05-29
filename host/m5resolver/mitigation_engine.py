from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field
from typing import Any

from .fastpath import FastPathSerializer
from .validation import IntentValidator, validate_intent_payload

logger = logging.getLogger("m5resolver.mitigation")

TELEMETRY_STREAM_PREFIX = "[TELEMETRY_STREAM]:"

DEFAULT_HEAP_CRITICAL_BYTES = 25_000
DEFAULT_JITTER_CRITICAL_MS = 50
DEFAULT_SAFE_FREQUENCY_HZ = 10
DEFAULT_REMEDIATION_STATE_MASK = 1
MITIGATION_COOLDOWN_S = 2.0


@dataclass
class MitigationStats:
    inspections: int = 0
    anomalies_detected: int = 0
    patches_emitted: int = 0
    last_patch_epoch: float = 0.0


class AutonomousMitigationEngine:
    """
    Telemetry-driven real-time remediation (Feature 53).

    Monitors device metrics against safety thresholds and synthesizes binwire
    fast-path throttling overrides when heap or scheduling jitter degrade.
    """

    def __init__(
        self,
        controller: Any,
        *,
        heap_critical_bytes: int = DEFAULT_HEAP_CRITICAL_BYTES,
        jitter_critical_ms: int = DEFAULT_JITTER_CRITICAL_MS,
        cooldown_s: float = MITIGATION_COOLDOWN_S,
    ) -> None:
        self.controller = controller
        self.validator = IntentValidator()
        self.heap_critical_bytes = heap_critical_bytes
        self.jitter_critical_ms = jitter_critical_ms
        self.cooldown_s = cooldown_s
        self.stats = MitigationStats()

    @staticmethod
    def parse_telemetry_line(line: str) -> dict[str, Any] | None:
        payload_text = line.strip()
        if payload_text.startswith(TELEMETRY_STREAM_PREFIX):
            payload_text = payload_text[len(TELEMETRY_STREAM_PREFIX) :].strip()
        if not payload_text.startswith("{"):
            return None
        try:
            return json.loads(payload_text)
        except json.JSONDecodeError:
            return None

    def inspect_telemetry_and_heal(self, raw_telemetry_packet: str | dict[str, Any]) -> bytes:
        self.stats.inspections += 1
        try:
            telemetry = (
                raw_telemetry_packet
                if isinstance(raw_telemetry_packet, dict)
                else self.parse_telemetry_line(raw_telemetry_packet)
            )
            if telemetry is None:
                return b""

            metrics = telemetry.get("metrics", {})
            if not isinstance(metrics, dict):
                return b""

            free_heap = int(metrics.get("free_heap", 100_000))
            task_jitter = int(metrics.get("task_jitter_ms", 0))

            if free_heap >= self.heap_critical_bytes and task_jitter <= self.jitter_critical_ms:
                return b""

            now = time.monotonic()
            if now - self.stats.last_patch_epoch < self.cooldown_s:
                return b""

            self.stats.anomalies_detected += 1
            logger.warning(
                "[ANOMALY DETECTED] Heap: %sB, Jitter: %sms — compiling remediation patch...",
                free_heap,
                task_jitter,
            )

            unit_id = int(telemetry.get("unit_id", metrics.get("active_unit_id", 0)))
            active_pin = int(telemetry.get("active_pin", metrics.get("active_pin", 0)))

            remediation_intent = {
                "intent": {
                    "action": "fast_track_gpio",
                    "parameters": {
                        "unit_id": unit_id,
                        "pin": active_pin,
                        "frequency_hz": DEFAULT_SAFE_FREQUENCY_HZ,
                        "state_mask": DEFAULT_REMEDIATION_STATE_MASK,
                    },
                },
                "fastpath": True,
            }

            errors = validate_intent_payload(remediation_intent)
            if errors:
                logger.error("[MITIGATION] Remediation intent rejected: %s", errors)
                return b""

            params = remediation_intent["intent"]["parameters"]
            frame = FastPathSerializer.pack_intent_vector(
                unit_id=params["unit_id"],
                pin=params["pin"],
                frequency=params["frequency_hz"],
                state=params["state_mask"],
            )
            self.stats.patches_emitted += 1
            self.stats.last_patch_epoch = now
            return frame

        except (json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
            logger.error("Failed to process telemetry packet signature: %s", exc)
            return b""

    def apply_heal_from_line(self, line: str) -> bool:
        """Parse line, compile remediation if needed, and inject via controller."""
        token = self.inspect_telemetry_and_heal(line)
        if not token:
            return False
        if self.controller is None or not getattr(self.controller, "is_open", False):
            return False
        self.controller.send_fastpath(token)
        logger.info("[MITIGATION] Auto-injected binwire remediation (%s bytes)", len(token))
        return True
