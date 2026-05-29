from pathlib import Path

from m5resolver.agent import AgenticController


def test_agent_remediation_on_error_status(tmp_path: Path):
    registry = tmp_path / "units.json"
    registry.write_text(
        '{"version":1,"units":[{"unit_id":"u1","bus":"internal","capabilities":["x"],"frequency_hz":20}]}',
        encoding="utf-8",
    )
    agent = AgenticController(registry_path=registry)
    corrective = agent.ingest_telemetry({"type": "telemetry", "status": "error", "metrics": {"free_heap": 10000}})
    assert corrective is not None
    assert "speaker" in corrective
