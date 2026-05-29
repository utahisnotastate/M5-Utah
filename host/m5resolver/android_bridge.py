"""Host-side contract mirror for Android FastPathUsbBridge wire layouts."""

from __future__ import annotations

import struct

from .binwire import BINWIRE_FRAME_LEN, BinwireEncoder
from .rpp_compiler import RPP_FRAME_LEN, HostRPPCompiler

ANDROID_BINWIRE_MAGIC = b"\x23\x23"
ANDROID_RPP_MAGIC = b"\x23\x50"
ANDROID_WIRE_STRUCT = "!BBHI"


def pack_android_binwire_frame(
    unit_id: int,
    pin_target: int,
    frequency_hz: int,
    state_mask: int,
) -> bytes:
    """Byte-identical to android WireFrames.BinwireFrame.pack()."""
    return BinwireEncoder.pack_unit_mutation(unit_id, pin_target, frequency_hz, state_mask)


def pack_android_rpp_frame(
    unit_id: int,
    opcode: int,
    data_vector: int,
    sequence_id: int,
) -> bytes:
    """Byte-identical to android WireFrames.RppFrame.pack()."""
    return HostRPPCompiler.compile_rpp_frame(unit_id, opcode, data_vector, sequence_id)


def unpack_android_wire_frame(frame: bytes) -> tuple[int, int, int, int]:
    if len(frame) < 10:
        raise ValueError("frame too short")
    if not (frame.startswith(ANDROID_BINWIRE_MAGIC) or frame.startswith(ANDROID_RPP_MAGIC)):
        raise ValueError("unrecognized android wire magic")
    return struct.unpack(ANDROID_WIRE_STRUCT, frame[2:10])
