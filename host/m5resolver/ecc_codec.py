from __future__ import annotations

import copy
import logging
from typing import Any

logger = logging.getLogger("m5resolver.ecc")

ECC_PROTECTED_WORDS = ("status_word", "battery_word", "heap_word")


class TelemetryECC:
    """
    Inline Hamming (7,4) codec for telemetry words.
    Detects and corrects single-bit corruption without retransmission.
    """

    @staticmethod
    def encode_nibble(nibble: int) -> int:
        nibble &= 0x0F
        d0 = (nibble >> 0) & 1
        d1 = (nibble >> 1) & 1
        d2 = (nibble >> 2) & 1
        d3 = (nibble >> 3) & 1
        p1 = d0 ^ d1 ^ d3
        p2 = d0 ^ d2 ^ d3
        p3 = d1 ^ d2 ^ d3
        return (
            (p1 << 0)
            | (p2 << 1)
            | (d0 << 2)
            | (p3 << 3)
            | (d1 << 4)
            | (d2 << 5)
            | (d3 << 6)
        ) & 0x7F

    @staticmethod
    def extract_nibble(encoded_word: int) -> int:
        encoded_word &= 0x7F
        d0 = (encoded_word >> 2) & 1
        d1 = (encoded_word >> 4) & 1
        d2 = (encoded_word >> 5) & 1
        d3 = (encoded_word >> 6) & 1
        return d0 | (d1 << 1) | (d2 << 2) | (d3 << 3)

    @staticmethod
    def decode_and_correct_word(encoded_7bit_packet: int) -> tuple[int, bool]:
        word = encoded_7bit_packet & 0x7F

        p1 = ((word >> 0) ^ (word >> 2) ^ (word >> 4) ^ (word >> 6)) & 0x01
        p2 = ((word >> 1) ^ (word >> 2) ^ (word >> 5) ^ (word >> 6)) & 0x01
        p3 = ((word >> 3) ^ (word >> 4) ^ (word >> 5) ^ (word >> 6)) & 0x01

        error_syndrome = p1 | (p2 << 1) | (p3 << 2)

        if error_syndrome != 0:
            logger.warning(
                "[ECC DETECTED] Noise anomaly identified at bit position: %s. Correcting bit value...",
                error_syndrome,
            )
            word ^= 1 << (error_syndrome - 1)
            return word, True

        return word, False

    @staticmethod
    def repair_telemetry_payload(telemetry: dict[str, Any]) -> tuple[dict[str, Any], bool]:
        repaired = copy.deepcopy(telemetry)
        ecc = repaired.get("ecc")
        if not isinstance(ecc, dict):
            return repaired, False

        any_fixed = False
        for key in ECC_PROTECTED_WORDS:
            raw = ecc.get(key)
            if not isinstance(raw, int):
                continue
            corrected, was_fixed = TelemetryECC.decode_and_correct_word(raw)
            ecc[key] = corrected
            if was_fixed:
                any_fixed = True
                ecc[f"{key}_repaired"] = True

        if any_fixed:
            repaired["ecc"] = ecc
            status_nibble = TelemetryECC.extract_nibble(int(ecc.get("status_word", 0)))
            status_map = {0: "operational", 1: "degraded", 2: "error"}
            if status_nibble in status_map:
                repaired["status"] = status_map[status_nibble]

            battery_nibble = TelemetryECC.extract_nibble(int(ecc.get("battery_word", 0)))
            if 0 <= battery_nibble <= 15:
                repaired["battery_pct"] = min(100, battery_nibble * 7)

        return repaired, any_fixed
