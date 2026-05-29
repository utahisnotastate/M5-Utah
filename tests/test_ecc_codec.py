import pytest

from m5resolver.ecc_codec import TelemetryECC


def test_encode_decode_round_trip():
    for nibble in range(16):
        encoded = TelemetryECC.encode_nibble(nibble)
        decoded, fixed = TelemetryECC.decode_and_correct_word(encoded)
        assert fixed is False
        assert TelemetryECC.extract_nibble(decoded) == nibble


def test_single_bit_correction():
    encoded = TelemetryECC.encode_nibble(0xA)
    corrupted = encoded ^ 0x04
    repaired, was_fixed = TelemetryECC.decode_and_correct_word(corrupted)
    assert was_fixed is True
    assert TelemetryECC.extract_nibble(repaired) == 0xA


def test_telemetry_fault_tolerance_contracts():
    """
    Asserts that ECC decoders trap and repair simulated single-bit line corruptions.
    """
    valid_word = TelemetryECC.encode_nibble(0x3)
    corrupted_packet_token = valid_word ^ 0x01

    repaired_data, was_fixed = TelemetryECC.decode_and_correct_word(corrupted_packet_token)

    assert was_fixed is True
    assert TelemetryECC.extract_nibble(repaired_data) == 0x3
    assert (repaired_data & 0x01) == (valid_word & 0x01)


def test_repair_telemetry_payload_restores_status():
    status_word = TelemetryECC.encode_nibble(1)
    corrupted = status_word ^ 0x02
    telemetry = {
        "type": "telemetry",
        "status": "operational",
        "battery_pct": 50,
        "ecc": {
            "status_word": corrupted,
            "battery_word": TelemetryECC.encode_nibble(7),
        },
    }
    repaired, any_fixed = TelemetryECC.repair_telemetry_payload(telemetry)
    assert any_fixed is True
    assert repaired["status"] == "degraded"
    assert repaired["ecc"]["status_word_repaired"] is True
