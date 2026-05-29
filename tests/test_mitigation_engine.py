import json

from m5resolver.mitigation_engine import (
    TELEMETRY_STREAM_PREFIX,
    AutonomousMitigationEngine,
)


def test_telemetry_stream_prefix_parsing():
    payload = {"metrics": {"free_heap": 50000, "task_jitter_ms": 2}}
    line = TELEMETRY_STREAM_PREFIX + json.dumps(payload)
    parsed = AutonomousMitigationEngine.parse_telemetry_line(line)
    assert parsed == payload


def test_mitigation_respects_cooldown():
    mitigator = AutonomousMitigationEngine(None, cooldown_s=60.0)
    degraded = {"metrics": {"free_heap": 10000, "task_jitter_ms": 80}}
    first = mitigator.inspect_telemetry_and_heal(degraded)
    second = mitigator.inspect_telemetry_and_heal(degraded)
    assert len(first) == 10
    assert second == b""
