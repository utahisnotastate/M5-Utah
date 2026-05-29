from __future__ import annotations

import logging
import struct
from typing import Any

logger = logging.getLogger("m5resolver.rpp")

RPP_MAGIC = b"\x23\x50"
RPP_STRUCT = "!BBHI"
RPP_FRAME_LEN = 2 + struct.calcsize(RPP_STRUCT)

# Functional execution opcodes understood by firmware MicroExecutionKernel / RPPDecoder
RPP_OPCODE_PIN_HIGH = 0x01
RPP_OPCODE_PIN_LOW = 0x02
RPP_OPCODE_SET_FREQUENCY = 0x03


class HostRPPCompiler:
    """
    Asymmetric Remote Procedure Piping (RPP).

    Flattens multi-layer intents into fixed-width `#P` frames (!BBHI layout)
    for zero-copy dispatch on the device micro-execution kernel.
    """

    @staticmethod
    def compile_rpp_frame(
        unit_id: int,
        functional_opcode: int,
        data_vector: int,
        sequence_id: int,
    ) -> bytes:
        payload = struct.pack(RPP_STRUCT, unit_id, functional_opcode, data_vector, sequence_id)
        logger.info(
            "[RPP COMPILER] Emitting token frame: Unit=%s Opcode=%s",
            unit_id,
            functional_opcode,
        )
        return RPP_MAGIC + payload

    @staticmethod
    def unpack_rpp_frame(frame: bytes) -> tuple[int, int, int, int]:
        if len(frame) < RPP_FRAME_LEN:
            raise ValueError(f"RPP frame too short: {len(frame)} bytes")
        if not frame.startswith(RPP_MAGIC):
            raise ValueError("RPP frame missing magic header")
        return struct.unpack(RPP_STRUCT, frame[2:RPP_FRAME_LEN])

    @staticmethod
    def encode_intent(intent: dict[str, Any]) -> bytes | None:
        block = intent.get("rpp")
        if not isinstance(block, dict):
            return None
        return HostRPPCompiler.compile_rpp_frame(
            int(block["unit_id"]),
            int(block.get("opcode", block.get("functional_opcode", 0))),
            int(block.get("data_vector", block.get("parameter", 0))),
            int(block.get("sequence_id", block.get("refresh_sequence_id", 0))),
        )

    @staticmethod
    def is_rpp_frame(data: bytes) -> bool:
        return len(data) >= 2 and data[:2] == RPP_MAGIC


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    binary_frame = HostRPPCompiler.compile_rpp_frame(
        unit_id=3, functional_opcode=12, data_vector=440, sequence_id=9821
    )
    logger.info("Compressed RPP segment output (hex): %s", binary_frame.hex())
