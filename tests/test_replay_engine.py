from m5resolver.replay_engine import HostReplayEngine, TIME_TRAVEL_PREFIX


def test_extract_journal_prefix():
    raw = (
        '[FLUXWIRE_TIME_TRAVEL_STREAM]:{"type":"time_travel_journal_dump",'
        '"journal_records":[{"allocated_heap_remaining":15000,"intent_fingerprint":"registry_hot_reload"}]}'
    )
    extracted = HostReplayEngine.extract_journal_json(raw)
    assert extracted is not None
    assert "time_travel_journal_dump" in extracted


def test_replay_detects_heap_fault():
    mock = (
        '{"type":"time_travel_journal_dump","journal_records":['
        '{"relative_ms":10,"allocated_heap_remaining":15000,"intent_fingerprint":"modify_unit:unbounded_buffer"}'
        "]}"
    )
    engine = HostReplayEngine()
    result = engine.reconstruct_hardware_crash_timeline(mock)
    assert result.ok is False
    assert result.fault_fingerprint == "modify_unit:unbounded_buffer"
    assert result.fault_heap == 15000


def test_replay_healthy_timeline():
    mock = (
        '{"type":"time_travel_journal_dump","journal_records":['
        '{"relative_ms":10,"allocated_heap_remaining":80000,"intent_fingerprint":"intent:display"}'
        "]}"
    )
    engine = HostReplayEngine()
    result = engine.reconstruct_hardware_crash_timeline(mock)
    assert result.ok is True
    assert result.records_analyzed == 1
