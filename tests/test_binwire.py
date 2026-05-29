import struct

import pytest

from m5resolver.binwire import BINWIRE_FRAME_LEN, BINWIRE_MAGIC, BINWIRE_STRUCT, BinwireEncoder


def test_binary_packing_integrity_contracts():
    """
    Asserts that the fast-path binary packing engine outputs the exact
    byte alignment and ordering requested by the firmware memory layout maps.
    """
    packed_frame = BinwireEncoder.pack_unit_mutation(unit_id=12, pin=22, frequency=400, state_flag=99)

    assert packed_frame.startswith(BINWIRE_MAGIC)
    assert len(packed_frame) == BINWIRE_FRAME_LEN

    unpacked_data = struct.unpack(BINWIRE_STRUCT, packed_frame[2:])

    assert unpacked_data[0] == 12
    assert unpacked_data[1] == 22
    assert unpacked_data[2] == 400
    assert unpacked_data[3] == 99


def test_unpack_round_trip():
    frame = BinwireEncoder.pack_unit_mutation(7, 10, 250, 412)
    assert BinwireEncoder.unpack_unit_mutation(frame) == (7, 10, 250, 412)


def test_encode_intent_from_binwire_block():
    intent = {
        "binwire": {
            "unit_id": 7,
            "pin": 10,
            "frequency": 250,
            "state_flag": 412,
        }
    }
    frame = BinwireEncoder.encode_intent(intent)
    assert frame is not None
    assert BinwireEncoder.unpack_unit_mutation(frame) == (7, 10, 250, 412)


def test_encode_intent_from_registry_units():
    intent = {
        "registry": {
            "units": {
                "display_matrix": {
                    "type": "SPI_DRV",
                    "pins": [18, 23, 5],
                    "frequency_hz": 4,
                    "refresh_sequence_id": 412,
                    "unit_id_num": 3,
                }
            }
        }
    }
    frame = BinwireEncoder.encode_intent(intent)
    assert frame is not None
    assert BinwireEncoder.unpack_unit_mutation(frame) == (3, 18, 4, 412)


def test_is_fastpath_frame():
    frame = BinwireEncoder.pack_unit_mutation(1, 2, 3, 4)
    assert BinwireEncoder.is_fastpath_frame(frame) is True
    assert BinwireEncoder.is_fastpath_frame(b'{"display":{}}') is False


def test_unpack_rejects_invalid_magic():
    with pytest.raises(ValueError, match="magic"):
        BinwireEncoder.unpack_unit_mutation(b"\x00\x00" + b"\x00" * 8)
