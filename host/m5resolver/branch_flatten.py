from __future__ import annotations

import logging
import struct

logger = logging.getLogger("m5resolver.flatten")

FLATTEN_MAGIC = b"\x23\x46"
FLATTEN_PAYLOAD = "!BBH"
FLATTEN_FRAME_LEN = 2 + struct.calcsize(FLATTEN_PAYLOAD)
MAX_JUMP_SLOTS = 16


class BranchFlattenCompiler:
    """
    Speculative branch flattening (m5-flatten).

    Compiles conditional state trees into index-mapped jump vectors (`#F` frames)
    for direct function-pointer dispatch on Core 1 without nested branch evaluation.
    """

    @staticmethod
    def compile_jump_vector(
        condition_id: int,
        target_function_slot: int,
        execution_tier: int,
    ) -> bytes:
        if not 0 <= condition_id <= 255:
            raise ValueError("condition_id must be 0..255")
        if not 0 <= target_function_slot < MAX_JUMP_SLOTS:
            raise ValueError(f"target_function_slot must be 0..{MAX_JUMP_SLOTS - 1}")
        if not 0 <= execution_tier <= 65535:
            raise ValueError("execution_tier must be 0..65535")

        packed_payload = struct.pack(
            FLATTEN_PAYLOAD,
            condition_id & 0xFF,
            target_function_slot & 0xFF,
            execution_tier & 0xFFFF,
        )
        logger.info(
            "[FLATTEN COMPILER] Flattening conditional path %d -> pointer function slot %d",
            condition_id,
            target_function_slot,
        )
        return FLATTEN_MAGIC + packed_payload

    @staticmethod
    def unpack_jump_vector(frame: bytes) -> tuple[int, int, int]:
        if len(frame) < FLATTEN_FRAME_LEN:
            raise ValueError("flatten frame too short")
        if not frame.startswith(FLATTEN_MAGIC):
            raise ValueError("flatten frame missing magic header")
        condition_id, function_slot, execution_tier = struct.unpack(
            FLATTEN_PAYLOAD, frame[2:FLATTEN_FRAME_LEN]
        )
        return condition_id, function_slot, execution_tier

    @staticmethod
    def is_flatten_frame(data: bytes) -> bool:
        return len(data) >= 2 and data[:2] == FLATTEN_MAGIC


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    binary_token = BranchFlattenCompiler.compile_jump_vector(
        condition_id=2, target_function_slot=7, execution_tier=3
    )
    print(f"Compressed Branch Overlay Output (Hex): {binary_token.hex()}")
