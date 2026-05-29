from __future__ import annotations

import logging
import struct
from typing import Any

logger = logging.getLogger("m5resolver.secure_wire")

# #A attestation wire (m5-secure). Magic 0x23 0x41 avoids collision with #S stream (0x23 0x53).
SECURE_WIRE_MAGIC = b"\x23\x41"
SECURE_WIRE_PAYLOAD = "!BBHI"
SECURE_WIRE_FRAME_LEN = 2 + struct.calcsize(SECURE_WIRE_PAYLOAD)


class SecureWireEncoder:
    """
    Cryptographic intent attestation (m5-secure).

    Binds monotonic sequence tokens to outbound fast-path frames to eliminate
    replay and injection vectors over serial and mesh transports.
    """

    def __init__(self, initial_sequence_id: int = 1000) -> None:
        self.current_sequence_id = initial_sequence_id

    def secure_pack_frame(
        self,
        target_unit_id: int,
        functional_opcode: int,
        data_vector: int,
    ) -> bytes:
        if not 0 <= target_unit_id <= 255:
            raise ValueError("target_unit_id must be 0..255")
        if not 0 <= functional_opcode <= 255:
            raise ValueError("functional_opcode must be 0..255")
        if not 0 <= data_vector <= 65535:
            raise ValueError("data_vector must be 0..65535")

        assigned_seq = self.current_sequence_id
        self.current_sequence_id += 1

        packed_payload = struct.pack(
            SECURE_WIRE_PAYLOAD,
            target_unit_id & 0xFF,
            functional_opcode & 0xFF,
            data_vector & 0xFFFF,
            assigned_seq & 0xFFFFFFFF,
        )
        logger.info(
            "[SECURE WIRE] Encoded frame sequence %s for unit %s",
            assigned_seq,
            target_unit_id,
        )
        return SECURE_WIRE_MAGIC + packed_payload

    def wrap_binwire_frame(self, frame: bytes) -> bytes:
        from .binwire import BinwireEncoder

        unit_id, pin, frequency, _seq = BinwireEncoder.unpack_unit_mutation(frame)
        return self.secure_pack_frame(unit_id, pin, frequency & 0xFFFF)

    def wrap_rpp_frame(self, frame: bytes) -> bytes:
        from .rpp_compiler import HostRPPCompiler

        unit_id, opcode, data_vector, _seq = HostRPPCompiler.unpack_rpp_frame(frame)
        return self.secure_pack_frame(unit_id, opcode, data_vector & 0xFFFF)

    @staticmethod
    def unpack_secure_frame(frame: bytes) -> tuple[int, int, int, int]:
        if len(frame) < SECURE_WIRE_FRAME_LEN:
            raise ValueError("secure wire frame too short")
        if not frame.startswith(SECURE_WIRE_MAGIC):
            raise ValueError("secure wire frame missing magic header")
        return struct.unpack(SECURE_WIRE_PAYLOAD, frame[2:SECURE_WIRE_FRAME_LEN])

    @staticmethod
    def is_secure_frame(data: bytes) -> bool:
        return len(data) >= 2 and data[:2] == SECURE_WIRE_MAGIC


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    encoder = SecureWireEncoder(initial_sequence_id=5000)
    print(encoder.secure_pack_frame(1, 4, 100).hex())
