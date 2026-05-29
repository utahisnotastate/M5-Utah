from __future__ import annotations

import logging
import struct
from typing import Any

logger = logging.getLogger("m5resolver.memory")

OVERLAY_MAGIC = b"\x23\x4d"
OVERLAY_HEADER = "!II"
OVERLAY_HEADER_LEN = 2 + struct.calcsize(OVERLAY_HEADER)

IRAM_EXEC_START = 0x40080000
IRAM_EXEC_END = 0x400A0000
MAX_OVERLAY_PAYLOAD = 4096


class HardwareMemoryCompiler:
    """
    Dynamic memory map overlays for localized IRAM instruction patches.
    """

    @staticmethod
    def verify_address_safety(address: int) -> bool:
        return IRAM_EXEC_START <= address <= IRAM_EXEC_END

    @staticmethod
    def compile_memory_overlay(target_address: int, machine_instructions: bytes) -> bytes:
        if not HardwareMemoryCompiler.verify_address_safety(target_address):
            raise ValueError(
                f"target address 0x{target_address:08X} outside IRAM fence "
                f"0x{IRAM_EXEC_START:08X}-0x{IRAM_EXEC_END:08X}"
            )
        if len(machine_instructions) > MAX_OVERLAY_PAYLOAD:
            raise ValueError(f"overlay payload exceeds {MAX_OVERLAY_PAYLOAD} bytes")

        payload_length = len(machine_instructions)
        metadata_header = struct.pack(OVERLAY_HEADER, target_address & 0xFFFFFFFF, payload_length)
        compressed_frame = OVERLAY_MAGIC + metadata_header + machine_instructions
        logger.info(
            "[COMPILER] Compiled %s bytes destined for target execution location: 0x%08X",
            payload_length,
            target_address,
        )
        return compressed_frame

    @staticmethod
    def unpack_memory_overlay(frame: bytes) -> tuple[int, bytes]:
        if len(frame) < OVERLAY_HEADER_LEN:
            raise ValueError("overlay frame too short")
        if not frame.startswith(OVERLAY_MAGIC):
            raise ValueError("overlay frame missing magic header")
        target_address, payload_length = struct.unpack(
            OVERLAY_HEADER, frame[2:OVERLAY_HEADER_LEN]
        )
        payload = frame[OVERLAY_HEADER_LEN : OVERLAY_HEADER_LEN + payload_length]
        if len(payload) != payload_length:
            raise ValueError("overlay frame truncated")
        return target_address, payload

    @staticmethod
    def validate_overlay_frame(frame: bytes) -> list[str]:
        errors: list[str] = []
        try:
            target_address, payload = HardwareMemoryCompiler.unpack_memory_overlay(frame)
        except ValueError as exc:
            return [str(exc)]
        if not HardwareMemoryCompiler.verify_address_safety(target_address):
            errors.append(f"overlay target 0x{target_address:08X} outside IRAM execution fence")
        if len(payload) > MAX_OVERLAY_PAYLOAD:
            errors.append("overlay payload too large")
        return errors

    @staticmethod
    def compile_unit_overlay(unit: dict[str, Any], *, default_address: int = IRAM_EXEC_START) -> bytes:
        payload_hex = unit.get("overlay_payload_hex") or unit.get("payload_hex")
        if isinstance(payload_hex, str):
            machine_instructions = bytes.fromhex(payload_hex)
        else:
            machine_instructions = unit.get("machine_instructions", b"")
            if isinstance(machine_instructions, str):
                machine_instructions = bytes.fromhex(machine_instructions)

        address = int(unit.get("target_address", unit.get("hook_address", default_address)))
        return HardwareMemoryCompiler.compile_memory_overlay(address, machine_instructions)
