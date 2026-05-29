from __future__ import annotations

import logging
import struct

logger = logging.getLogger("m5resolver.stream_packer")

STREAM_MAGIC = b"\x23\x53"
STREAM_PAYLOAD = "!BBH"
STREAM_FRAME_LEN = 2 + struct.calcsize(STREAM_PAYLOAD)


class HostStreamPacker:
    """
    Asymmetric zero-copy stream packaging.

    Emits fixed-width `#S` frames aligned with CrossCorePipe ring ingest on
    Core 0 and deterministic Core 1 stream dispatch.
    """

    @staticmethod
    def pack_stream_frame(
        unit_id: int,
        operational_mode: int,
        baseline_frequency: int,
    ) -> bytes:
        if not 0 <= unit_id <= 255:
            raise ValueError("unit_id must be 0..255")
        if not 0 <= operational_mode <= 255:
            raise ValueError("operational_mode must be 0..255")
        if not 0 <= baseline_frequency <= 65535:
            raise ValueError("baseline_frequency must be 0..65535")

        packed_payload = struct.pack(
            STREAM_PAYLOAD,
            unit_id & 0xFF,
            operational_mode & 0xFF,
            baseline_frequency & 0xFFFF,
        )
        logger.info(
            "[STREAM PACKER] Generated binary token for unit %d. mode=%d",
            unit_id,
            operational_mode,
        )
        return STREAM_MAGIC + packed_payload

    @staticmethod
    def unpack_stream_frame(frame: bytes) -> tuple[int, int, int]:
        if len(frame) < STREAM_FRAME_LEN:
            raise ValueError("stream frame too short")
        if not frame.startswith(STREAM_MAGIC):
            raise ValueError("stream frame missing magic header")
        return struct.unpack(STREAM_PAYLOAD, frame[2:STREAM_FRAME_LEN])

    @staticmethod
    def is_stream_frame(data: bytes) -> bool:
        return len(data) >= 2 and data[:2] == STREAM_MAGIC


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    binary_token = HostStreamPacker.pack_stream_frame(
        unit_id=8, operational_mode=1, baseline_frequency=120
    )
    print(f"Compressed Stream Segment Payload (Hex): {binary_token.hex()}")
