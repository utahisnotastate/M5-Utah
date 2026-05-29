from m5resolver.delta_engine import DeltaEncoder


def test_delta_round_trip():
    updates = {0: 100, 2: 440, 5: 880}
    frame = DeltaEncoder.pack_delta(updates, transaction_sequence_id=7)
    seq, bitmask, decoded = DeltaEncoder.unpack_delta(frame)
    assert seq == 7
    assert decoded == updates
    assert bitmask == (1 << 0) | (1 << 2) | (1 << 5)


def test_bitmap_delta_round_trip():
    from m5resolver.delta_engine import BitmappedDeltaCompiler

    frame = BitmappedDeltaCompiler.compile_bitmap_delta(2, 250, 1024)
    bitmask, frequency, sequence = BitmappedDeltaCompiler.unpack_bitmap_delta(frame)
    assert bitmask == 1 << 2
    assert frequency == 250
    assert sequence == 1024
    assert len(frame) == 10


def test_graph_mutation_encoding():
    units = {
        "imu_sensor_core": {"frequency_hz": 50, "slot_id": 0},
        "dsp_filter_unit": {
            "frequency_hz": 100,
            "slot_id": 1,
            "depends_on": ["imu_sensor_core"],
        },
    }
    frame = DeltaEncoder.encode_graph_mutation(units, "imu_sensor_core", transaction_sequence_id=3)
    assert frame is not None
    _, _, decoded = DeltaEncoder.unpack_delta(frame)
    assert decoded[0] == 50
    assert decoded[1] == 100
