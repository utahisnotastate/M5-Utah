from __future__ import annotations

import logging
import struct

logger = logging.getLogger("m5resolver.vector_compiler")

VECTOR_MAGIC = b"\x23\x49"
VECTOR_HEADER = "!BHI"
VECTOR_HEADER_LEN = 2 + struct.calcsize(VECTOR_HEADER)
MAX_VECTOR_CHANNELS = 4
MAX_VECTOR_PATCH_BYTES = 512


class HostVectorCompiler:
    """
    Dynamic interrupt vector patching (m5-vectorfence).

    Compiles peripheral ISR targets into `#I` wire frames with IRAM-bound
    position-independent machine code payloads.
    """

    @staticmethod
    def compile_vector_overlay(
        interrupt_source_id: int,
        byte_length: int,
        transaction_id: int,
    ) -> bytes:
        if not 0 <= interrupt_source_id < MAX_VECTOR_CHANNELS:
            raise ValueError(f"interrupt_source_id must be 0..{MAX_VECTOR_CHANNELS - 1}")
        if not 0 < byte_length <= MAX_VECTOR_PATCH_BYTES:
            raise ValueError(f"byte_length must be 1..{MAX_VECTOR_PATCH_BYTES}")
        if not 0 <= transaction_id <= 0xFFFFFFFF:
            raise ValueError("transaction_id out of range")

        metadata_header = struct.pack(
            VECTOR_HEADER,
            interrupt_source_id & 0xFF,
            byte_length & 0xFFFF,
            transaction_id & 0xFFFFFFFF,
        )
        logger.info(
            "[VECTOR COMPILER] Packing IRAM overlay for interrupt source channel: %d",
            interrupt_source_id,
        )
        return VECTOR_MAGIC + metadata_header

    @staticmethod
    def compile_vector_patch(
        interrupt_source_id: int,
        machine_code: bytes,
        *,
        transaction_id: int = 1,
    ) -> bytes:
        if len(machine_code) == 0:
            raise ValueError("machine_code must not be empty")
        header = HostVectorCompiler.compile_vector_overlay(
            interrupt_source_id, len(machine_code), transaction_id
        )
        return header + machine_code

    @staticmethod
    def unpack_vector_overlay(frame: bytes) -> tuple[int, int, int]:
        if len(frame) < VECTOR_HEADER_LEN:
            raise ValueError("vector frame too short")
        if not frame.startswith(VECTOR_MAGIC):
            raise ValueError("vector frame missing magic header")
        channel, byte_length, transaction_id = struct.unpack(
            VECTOR_HEADER, frame[2:VECTOR_HEADER_LEN]
        )
        return channel, byte_length, transaction_id

    @staticmethod
    def is_vector_frame(data: bytes) -> bool:
        return len(data) >= 2 and data[:2] == VECTOR_MAGIC


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    binary_frame = HostVectorCompiler.compile_vector_overlay(
        interrupt_source_id=2, byte_length=256, transaction_id=2026
    )
    print(f"Generated Vector Overlay Frame (Hex): {binary_frame.hex()}")
