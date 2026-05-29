from __future__ import annotations

import logging
import struct
from typing import Any

logger = logging.getLogger("m5resolver.delta")

DELTA_MAGIC = b"\xde\xda"
DELTA_HEADER = "!BH"
DELTA_HEADER_LEN = 2 + struct.calcsize(DELTA_HEADER)
BITMAP_DELTA_MAGIC = b"\x23\x44"
BITMAP_DELTA_PAYLOAD = "!HHI"
BITMAP_DELTA_FRAME_LEN = 2 + struct.calcsize(BITMAP_DELTA_PAYLOAD)
MAX_DELTA_SLOTS = 16


class BitmappedDeltaCompiler:
    """
    Bitmapped structural state overlays (Feature 60).

    Flattens single-slot configuration mutations into fixed-width binary tokens
    for zero-allocation mesh broadcast (`##D` magic, 10-byte frames).
    """

    @staticmethod
    def compile_bitmap_delta(
        slot_id: int,
        operational_frequency: int,
        sequence_id: int,
    ) -> bytes:
        if slot_id < 0 or slot_id >= MAX_DELTA_SLOTS:
            raise ValueError(f"slot_id must be 0..{MAX_DELTA_SLOTS - 1}, got {slot_id}")
        bitmask = 1 << slot_id
        packed_payload = struct.pack(
            BITMAP_DELTA_PAYLOAD,
            bitmask & 0xFFFF,
            operational_frequency & 0xFFFF,
            sequence_id & 0xFFFFFFFF,
        )
        logger.info(
            "[DELTA COMPILER] Generated structural overlay mask: 0x%04X for slot %d",
            bitmask,
            slot_id,
        )
        return BITMAP_DELTA_MAGIC + packed_payload

    @staticmethod
    def unpack_bitmap_delta(frame: bytes) -> tuple[int, int, int]:
        if len(frame) < BITMAP_DELTA_FRAME_LEN:
            raise ValueError("bitmap delta frame too short")
        if not frame.startswith(BITMAP_DELTA_MAGIC):
            raise ValueError("bitmap delta frame missing magic header")
        bitmask, frequency, sequence_id = struct.unpack(BITMAP_DELTA_PAYLOAD, frame[2:])
        return bitmask, frequency, sequence_id

    @staticmethod
    def is_bitmap_delta_frame(data: bytes) -> bool:
        return len(data) >= 2 and data[:2] == BITMAP_DELTA_MAGIC


class DeltaEncoder:
    """Run-length bitmapped structural state compression for registry hot-patches."""

    @staticmethod
    def pack_delta(
        slot_updates: dict[int, int],
        *,
        transaction_sequence_id: int = 1,
    ) -> bytes:
        bitmask = 0
        ordered_slots: list[int] = []
        for slot_id in range(MAX_DELTA_SLOTS):
            if slot_id in slot_updates:
                bitmask |= 1 << slot_id
                ordered_slots.append(slot_id)

        header = struct.pack(DELTA_HEADER, transaction_sequence_id & 0xFF, bitmask & 0xFFFF)
        payload = bytearray(DELTA_MAGIC + header)
        for slot_id in ordered_slots:
            freq = slot_updates[slot_id] & 0xFFFF
            payload.extend(struct.pack("!H", freq))
        return bytes(payload)

    @staticmethod
    def unpack_delta(frame: bytes) -> tuple[int, int, dict[int, int]]:
        if len(frame) < DELTA_HEADER_LEN:
            raise ValueError("delta frame too short")
        if not frame.startswith(DELTA_MAGIC):
            raise ValueError("delta frame missing magic header")
        seq_id, bitmask = struct.unpack(DELTA_HEADER, frame[2:DELTA_HEADER_LEN])
        updates: dict[int, int] = {}
        offset = DELTA_HEADER_LEN
        for slot_id in range(MAX_DELTA_SLOTS):
            if (bitmask >> slot_id) & 0x01:
                if offset + 2 > len(frame):
                    raise ValueError("delta frame truncated")
                (freq,) = struct.unpack("!H", frame[offset : offset + 2])
                updates[slot_id] = freq
                offset += 2
        return seq_id, bitmask, updates

    @staticmethod
    def encode_graph_mutation(
        graph_units: dict[str, dict[str, Any]],
        changed_node: str,
        *,
        transaction_sequence_id: int = 1,
    ) -> bytes | None:
        from .graph_engine import StateGraphEngine

        graph = StateGraphEngine.from_units(graph_units)
        if graph.validate_dag():
            return None
        cascade = graph.compute_mutation_delta_paths(changed_node)
        slot_map = graph.build_slot_frequency_map(cascade, graph_units)
        if not slot_map:
            return None
        return DeltaEncoder.pack_delta(slot_map, transaction_sequence_id=transaction_sequence_id)

    @staticmethod
    def is_delta_frame(data: bytes) -> bool:
        return len(data) >= 2 and data[:2] == DELTA_MAGIC


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    binary_token = BitmappedDeltaCompiler.compile_bitmap_delta(
        slot_id=2, operational_frequency=250, sequence_id=1024
    )
    print(f"Compressed Delta Packet Stream (Hex): {binary_token.hex()}")
