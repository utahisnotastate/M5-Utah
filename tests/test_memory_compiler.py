import struct

import pytest

from m5resolver.memory_compiler import (
    HardwareMemoryCompiler,
    IRAM_EXEC_END,
    IRAM_EXEC_START,
    MAX_OVERLAY_PAYLOAD,
    OVERLAY_HEADER,
    OVERLAY_HEADER_LEN,
    OVERLAY_MAGIC,
)


def test_compile_memory_overlay_frame_layout():
    instructions = b"\x00\x11\x22\x33\x44\x55"
    target = 0x40080000
    frame = HardwareMemoryCompiler.compile_memory_overlay(target, instructions)

    assert frame.startswith(OVERLAY_MAGIC)
    address, length = struct.unpack(OVERLAY_HEADER, frame[2:OVERLAY_HEADER_LEN])
    assert address == target
    assert length == len(instructions)
    assert frame[OVERLAY_HEADER_LEN:] == instructions


def test_unpack_memory_overlay_round_trip():
    instructions = b"\xde\xad\xbe\xef"
    target = 0x40090000
    frame = HardwareMemoryCompiler.compile_memory_overlay(target, instructions)
    unpacked_address, unpacked_payload = HardwareMemoryCompiler.unpack_memory_overlay(frame)
    assert unpacked_address == target
    assert unpacked_payload == instructions


def test_validate_overlay_frame_rejects_out_of_bounds():
    bad_address = 0x3FF00000
    frame = OVERLAY_MAGIC + struct.pack(OVERLAY_HEADER, bad_address, 4) + b"\x00" * 4
    errors = HardwareMemoryCompiler.validate_overlay_frame(frame)
    assert any("outside IRAM execution fence" in e for e in errors)


def test_compile_unit_overlay_from_hex():
    unit = {
        "target_address": IRAM_EXEC_START,
        "overlay_payload_hex": "00112233",
    }
    frame = HardwareMemoryCompiler.compile_unit_overlay(unit)
    _, payload = HardwareMemoryCompiler.unpack_memory_overlay(frame)
    assert payload == bytes.fromhex("00112233")


def test_overlay_payload_size_limit():
    oversized = b"\x00" * (MAX_OVERLAY_PAYLOAD + 1)
    with pytest.raises(ValueError, match="exceeds"):
        HardwareMemoryCompiler.compile_memory_overlay(IRAM_EXEC_START, oversized)


def test_iram_fence_constants():
    assert IRAM_EXEC_START == 0x40080000
    assert IRAM_EXEC_END == 0x400A0000
