from __future__ import annotations

import json
import logging
import struct
from typing import Any

logger = logging.getLogger("m5resolver.binwire")

BINWIRE_MAGIC = b"\x23\x23"
BINWIRE_STRUCT = "!BBHI"
BINWIRE_FRAME_LEN = 2 + struct.calcsize(BINWIRE_STRUCT)


class BinwireEncoder:
    """
    Binary fast-path compression for deterministic ESP32 execution.

    Host validates JSON against schemas; transport may use fixed-width binary
    frames instead of verbose JSON strings on the wire.
    """

    @staticmethod
    def pack_unit_mutation(unit_id: int, pin: int, frequency: int, state_flag: int) -> bytes:
        payload = struct.pack(BINWIRE_STRUCT, unit_id, pin, frequency, state_flag)
        return BINWIRE_MAGIC + payload

    @staticmethod
    def unpack_unit_mutation(frame: bytes) -> tuple[int, int, int, int]:
        if len(frame) < BINWIRE_FRAME_LEN:
            raise ValueError(f"binwire frame too short: {len(frame)} bytes")
        if not frame.startswith(BINWIRE_MAGIC):
            raise ValueError("binwire frame missing magic header")
        return struct.unpack(BINWIRE_STRUCT, frame[2 : BINWIRE_FRAME_LEN])

    @staticmethod
    def encode_intent(intent: dict[str, Any]) -> bytes | None:
        """Build a fast-path frame from a validated intent payload."""
        block = intent.get("binwire")
        if isinstance(block, dict):
            return BinwireEncoder.pack_unit_mutation(
                int(block["unit_id"]),
                int(block["pin"]),
                int(block.get("frequency", block.get("frequency_hz", 2))),
                int(block.get("state_flag", block.get("refresh_sequence_id", 0))),
            )

        registry = intent.get("registry")
        if not isinstance(registry, dict):
            return None

        units = registry.get("units")
        if isinstance(units, dict):
            for idx, (unit_key, unit_cfg) in enumerate(units.items()):
                if not isinstance(unit_cfg, dict):
                    continue
                pin = _first_pin(unit_cfg)
                frequency = int(unit_cfg.get("frequency_hz", 2))
                seq = int(unit_cfg.get("refresh_sequence_id", 0))
                unit_id = int(unit_cfg.get("unit_id_num", idx))
                return BinwireEncoder.pack_unit_mutation(unit_id, pin, frequency, seq)

        if isinstance(units, list):
            for idx, unit_cfg in enumerate(units):
                if not isinstance(unit_cfg, dict):
                    continue
                pin = _first_pin(unit_cfg)
                frequency = int(unit_cfg.get("frequency_hz", 2))
                seq = int(unit_cfg.get("refresh_sequence_id", 0))
                unit_id = int(unit_cfg.get("unit_id_num", idx))
                return BinwireEncoder.pack_unit_mutation(unit_id, pin, frequency, seq)

        return None

    @staticmethod
    def is_fastpath_frame(data: bytes) -> bool:
        return len(data) >= 2 and data[:2] == BINWIRE_MAGIC


def _first_pin(unit_cfg: dict[str, Any]) -> int:
    pins = unit_cfg.get("pins")
    if isinstance(pins, list) and pins:
        return int(pins[0])
    pin = unit_cfg.get("pin")
    if pin is not None:
        return int(pin)
    return 0


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    packed = BinwireEncoder.pack_unit_mutation(unit_id=7, pin=10, frequency=250, state_flag=412)
    logger.info("[BINWIRE] Compressed state token frame (hex): %s", packed.hex())
    sample = {
        "binwire": {"unit_id": 7, "pin": 10, "frequency": 250, "state_flag": 412},
    }
    logger.info("[BINWIRE] Intent encode: %s", BinwireEncoder.encode_intent(sample).hex())
