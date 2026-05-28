from pathlib import Path

from m5resolver.registry import DriverRegistry


def test_registry_loads_and_lists_ids():
    base = Path(__file__).resolve().parents[1]
    reg = DriverRegistry(base / "registry" / "units.json")
    reg.load()
    ids = reg.list_ids()
    assert "env4" in ids
    assert "imu_builtin" in ids
