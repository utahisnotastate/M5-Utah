import pytest

from m5resolver.memory_profiler import DEFAULT_HANDLE_POOL_BYTES, HostMemoryProfiler
from m5resolver.validation import validate_intent_payload


def test_evaluate_payload_safety_rejects_near_limit():
    profiler = HostMemoryProfiler()
    hazardous_unit = {"type": "stream_processor", "buffer_size_bytes": 512}
    assert profiler.evaluate_payload_safety(hazardous_unit, current_device_heap_top=1600) is False


def test_evaluate_payload_safety_accepts_headroom():
    profiler = HostMemoryProfiler()
    safe_unit = {"type": "sensor_node", "buffer_size_bytes": 128}
    assert profiler.evaluate_payload_safety(safe_unit, current_device_heap_top=256) is True


def test_evaluate_registry_units_duplicate_handle():
    profiler = HostMemoryProfiler()
    units = {
        "a": {"allocation_handle_id": 2, "buffer_size_bytes": 64},
        "b": {"allocation_handle_id": 2, "buffer_size_bytes": 64},
    }
    errors = profiler.evaluate_registry_units(units)
    assert any("duplicate allocation_handle_id" in e for e in errors)


def test_should_request_compaction():
    profiler = HostMemoryProfiler()
    profiler.estimated_pool_top = 1700
    assert profiler.should_request_compaction({"u1": {"buffer_size_bytes": 256}}) is True


def test_update_device_snapshot_reads_metrics():
    profiler = HostMemoryProfiler()
    profiler.update_device_snapshot(
        {
            "metrics": {
                "free_heap": 28000,
                "handle_pool_top": 512,
                "handle_fragmentation_index": 0.12,
            }
        }
    )
    assert profiler.device_free_heap == 28000
    assert profiler.estimated_pool_top == 512
    assert profiler.estimated_fragmentation_index == pytest.approx(0.12)


def test_memory_compact_intent_validates():
    assert validate_intent_payload({"memory_compact": True}) == []


def test_invalid_allocation_handle_rejected():
    payload = {
        "registry": {
            "units": {
                "bad": {"allocation_handle_id": 99, "buffer_size_bytes": 64},
            }
        }
    }
    errors = validate_intent_payload(payload)
    assert any("allocation_handle_id" in e for e in errors)


def test_default_pool_limit_matches_firmware():
    assert DEFAULT_HANDLE_POOL_BYTES == 2048
