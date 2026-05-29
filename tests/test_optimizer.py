from m5resolver.optimizer import HardwareCostModel


def test_prune_intent_marks_registry_units():
    intent = {
        "registry": {
            "units": {
                "dsp_worker": {
                    "type": "dsp_worker",
                    "frequency_hz": 50000,
                    "buffer_size_bytes": 8192,
                }
            }
        }
    }
    pruned, was_pruned = HardwareCostModel.prune_intent(intent, available_heap_bytes=16000)
    assert was_pruned is True
    assert pruned["resource_pruned"] is True
    unit = pruned["registry"]["units"]["dsp_worker"]
    assert unit["frequency_hz"] < 50000
    assert unit.get("pruned_by_gatekeeper") is True


def test_safe_intent_not_pruned():
    intent = {
        "registry": {
            "units": {
                "heartbeat": {"frequency_hz": 2, "buffer_size_bytes": 128},
            }
        }
    }
    pruned, was_pruned = HardwareCostModel.prune_intent(intent, available_heap_bytes=32000)
    assert was_pruned is False
    assert "resource_pruned" not in pruned
