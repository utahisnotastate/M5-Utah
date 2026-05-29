from __future__ import annotations

import binascii
import logging
import struct
from typing import Any

logger = logging.getLogger("m5resolver.remediation")

REMEDIATION_MAGIC = b"\x23\x52"
REMEDIATION_PAYLOAD = "!BBH"
REMEDIATION_FRAME_LEN = 2 + struct.calcsize(REMEDIATION_PAYLOAD)
HEALTH_VITALS_STREAM_PREFIX = "[HEALTH_VITALS_STREAM]:"
HEALTH_VITALS_STRUCT = "!BIB"
HEALTH_VITALS_LEN = struct.calcsize(HEALTH_VITALS_STRUCT)

DEFAULT_HEAP_CRITICAL_BYTES = 25_000
DEFAULT_JITTER_CRITICAL_MS = 50
DEFAULT_SAFE_FREQUENCY_HZ = 10
DEFAULT_FALLBACK_SAFETY_PIN = 0


class AutonomousRemediationEngine:
    """
    Closed-loop telemetry overrides (m5-autofence).

    Evaluates hardware vitals against safety perimeters and synthesizes `#R`
    defensive fast-path remediation frames for instant wire injection.
    """

    def __init__(
        self,
        *,
        heap_critical_bytes: int = DEFAULT_HEAP_CRITICAL_BYTES,
        jitter_critical_ms: int = DEFAULT_JITTER_CRITICAL_MS,
        safe_frequency_hz: int = DEFAULT_SAFE_FREQUENCY_HZ,
    ) -> None:
        self.heap_critical_bytes = heap_critical_bytes
        self.jitter_critical_ms = jitter_critical_ms
        self.safe_frequency_hz = safe_frequency_hz

    @staticmethod
    def compile_remediation_token(
        unit_id: int,
        *,
        safety_pin: int = DEFAULT_FALLBACK_SAFETY_PIN,
        throttled_frequency: int = DEFAULT_SAFE_FREQUENCY_HZ,
    ) -> bytes:
        packed_payload = struct.pack(
            REMEDIATION_PAYLOAD,
            unit_id & 0xFF,
            safety_pin & 0xFF,
            throttled_frequency & 0xFFFF,
        )
        return REMEDIATION_MAGIC + packed_payload

    @staticmethod
    def unpack_remediation_token(frame: bytes) -> tuple[int, int, int]:
        if len(frame) < REMEDIATION_FRAME_LEN:
            raise ValueError("remediation frame too short")
        if not frame.startswith(REMEDIATION_MAGIC):
            raise ValueError("remediation frame missing magic header")
        return struct.unpack(REMEDIATION_PAYLOAD, frame[2:REMEDIATION_FRAME_LEN])

    @staticmethod
    def parse_vitals_line(line: str) -> tuple[int, int, int] | None:
        text = line.strip()
        if not text.startswith(HEALTH_VITALS_STREAM_PREFIX):
            return None
        payload = text[len(HEALTH_VITALS_STREAM_PREFIX) :].strip()
        try:
            raw = binascii.unhexlify(payload)
        except (binascii.Error, ValueError):
            return None
        if len(raw) != HEALTH_VITALS_LEN:
            return None
        unit_id, free_heap, jitter = struct.unpack(HEALTH_VITALS_STRUCT, raw)
        return int(unit_id), int(free_heap), int(jitter)

    @staticmethod
    def encode_vitals_line(unit_id: int, free_heap_bytes: int, task_jitter_ms: int) -> str:
        raw = struct.pack(
            HEALTH_VITALS_STRUCT,
            unit_id & 0xFF,
            free_heap_bytes & 0xFFFFFFFF,
            task_jitter_ms & 0xFF,
        )
        return HEALTH_VITALS_STREAM_PREFIX + binascii.hexlify(raw).decode("ascii")

    def inspect_and_heal_profile(
        self,
        unit_id: int,
        free_heap_bytes: int,
        task_jitter_ms: int,
    ) -> tuple[bytes, bool]:
        if (
            free_heap_bytes >= self.heap_critical_bytes
            and task_jitter_ms <= self.jitter_critical_ms
        ):
            return b"", False

        logger.warning(
            "[ANOMALY] Unit %s performance slipped! Heap: %sB, Jitter: %sms. Compiling fix...",
            unit_id,
            free_heap_bytes,
            task_jitter_ms,
        )
        token = self.compile_remediation_token(
            unit_id,
            safety_pin=DEFAULT_FALLBACK_SAFETY_PIN,
            throttled_frequency=self.safe_frequency_hz,
        )
        return token, True

    def inspect_from_telemetry(self, telemetry: dict[str, Any]) -> tuple[bytes, bool]:
        metrics = telemetry.get("metrics", {})
        if not isinstance(metrics, dict):
            metrics = telemetry
        unit_id = int(
            telemetry.get("unit_id", metrics.get("active_unit_id", metrics.get("unit_id", 0)))
        )
        free_heap = int(metrics.get("free_heap", 100_000))
        jitter = int(metrics.get("task_jitter_ms", 0))
        return self.inspect_and_heal_profile(unit_id, free_heap, jitter)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    engine = AutonomousRemediationEngine()
    remediation_token, was_triggered = engine.inspect_and_heal_profile(
        unit_id=7, free_heap_bytes=18500, task_jitter_ms=65
    )
    print(f"Self-Repair Active: {was_triggered} | Token Output (Hex): {remediation_token.hex()}")
