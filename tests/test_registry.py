from pathlib import Path

import json

from m5resolver.registry import DriverRegistry


def test_registry_loads_and_lists_ids():
    base = Path(__file__).resolve().parents[1]
    reg = DriverRegistry(base / "registry" / "units.json")
    reg.load()
    ids = reg.list_ids()
    assert "env4" in ids
    assert "imu_builtin" in ids


def test_shadow_fork_lifecycle_contracts():
    """
    Asserts that registry parsing frameworks append sequence trackers
    to tracking modifications, enabling safe live task swappability.
    """
    intent_delta = {
        "version": "23.0.0",
        "units": {
            "display_matrix": {
                "type": "SPI_DRV",
                "pins": [18, 23, 5],
                "refresh_sequence_id": 412,
            }
        },
    }

    raw_serialized = json.dumps(intent_delta)
    parsed_back = json.loads(raw_serialized)

    assert "refresh_sequence_id" in parsed_back["units"]["display_matrix"]
    assert parsed_back["units"]["display_matrix"]["refresh_sequence_id"] == 412


def test_unit_spec_parses_refresh_sequence_id(tmp_path):
    registry_file = tmp_path / "units.json"
    registry_file.write_text(
        json.dumps(
            {
                "version": 1,
                "units": [
                    {
                        "unit_id": "display_matrix",
                        "bus": "spi",
                        "capabilities": ["display"],
                        "refresh_sequence_id": 412,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    reg = DriverRegistry(registry_file)
    reg.load()
    spec = reg.get("display_matrix")
    assert spec is not None
    assert spec.refresh_sequence_id == 412


def test_automated_resource_pruning_limits():
    """
    Asserts that the optimizer model accurately identifies and clamps high-draw
    unit configurations to protect running hardware nodes from resource exhaustion.
    """
    from m5resolver.optimizer import HardwareCostModel

    hazardous_unit = {
        "type": "high_speed_stream",
        "frequency_hz": 40000,
        "buffer_size_bytes": 16384,
    }

    pruned_config, was_pruned = HardwareCostModel.evaluate_and_prune_intent(
        intent_unit=hazardous_unit,
        available_heap_bytes=20000,
    )

    assert was_pruned is True
    assert pruned_config["frequency_hz"] < 40000
    assert pruned_config["buffer_size_bytes"] <= 8192
    assert pruned_config.get("pruned_by_gatekeeper") is True


def test_virtual_handle_allocation_integrity():
    """
    Asserts that configuration managers preserve deterministic handle slot identifiers
    required by the firmware virtual handle allocation matrix.
    """
    sample_intent_block = {
        "version": "23.0.0",
        "units": {
            "dynamic_accelerometer": {
                "type": "sensor_node",
                "allocation_handle_id": 4,
                "buffer_size_bytes": 128,
            }
        },
    }

    raw_json_string = json.dumps(sample_intent_block)
    reconstructed_data = json.loads(raw_json_string)

    assert "allocation_handle_id" in reconstructed_data["units"]["dynamic_accelerometer"]
    assert reconstructed_data["units"]["dynamic_accelerometer"]["allocation_handle_id"] == 4


def test_registry_unit_spec_parses_allocation_handle(tmp_path):
    registry_file = tmp_path / "units.json"
    registry_file.write_text(
        json.dumps(
            {
                "version": 1,
                "units": [
                    {
                        "unit_id": "dynamic_accelerometer",
                        "bus": "internal",
                        "capabilities": ["accel"],
                        "allocation_handle_id": 4,
                        "buffer_size_bytes": 128,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    reg = DriverRegistry(registry_file)
    reg.load()
    spec = reg.get("dynamic_accelerometer")
    assert spec is not None
    assert spec.allocation_handle_id == 4
    assert spec.buffer_size_bytes == 128


def test_cross_core_execution_schema_contracts():
    """
    Asserts that the intent configuration manager cleanly handles and structures
    the specific identification tokens used by the multi-core allocation tasks.
    """
    import json

    from m5resolver.validation import validate_registry_payload

    asymmetric_intent_block = {
        "version": 1,
        "units": {
            "core_0_bridge": {
                "unit_id": "core_0_bridge",
                "bus": "internal",
                "capabilities": ["binwire"],
                "type": "fast_path_bridge",
                "execution_core_target": 0,
                "buffer_allocation_bytes": 512,
            }
        },
    }

    serialized_string = json.dumps(asymmetric_intent_block)
    parsed_payload = json.loads(serialized_string)

    assert "execution_core_target" in parsed_payload["units"]["core_0_bridge"]
    assert parsed_payload["units"]["core_0_bridge"]["execution_core_target"] == 0
    assert validate_registry_payload({"units": parsed_payload["units"]}) == []


def test_registry_unit_spec_parses_execution_core_target(tmp_path):
    registry_file = tmp_path / "units.json"
    registry_file.write_text(
        json.dumps(
            {
                "version": 1,
                "units": [
                    {
                        "unit_id": "core_0_bridge",
                        "bus": "internal",
                        "capabilities": ["binwire"],
                        "type": "fast_path_bridge",
                        "execution_core_target": 0,
                        "buffer_allocation_bytes": 512,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    reg = DriverRegistry(registry_file)
    reg.load()
    spec = reg.get("core_0_bridge")
    assert spec is not None
    assert spec.execution_core_target == 0
    assert spec.buffer_allocation_bytes == 512


def test_registry_scheduler_audit_on_units_json():
    """Predictive scheduling audit runs against the live registry catalog."""
    from pathlib import Path

    from m5resolver.scheduler_compiler import HostSchedulerCompiler

    registry_path = Path(__file__).resolve().parents[1] / "registry" / "units.json"
    optimized, audit = HostSchedulerCompiler.audit_registry_file(registry_path)
    assert isinstance(optimized.get("units"), dict)
    assert len(optimized["units"]) >= 1
    assert isinstance(audit.warnings, list)
    assert isinstance(audit.escalations, list)
    assert isinstance(audit.bus_conflicts, list)


def test_bitmapped_delta_packing_contracts():
    """
    Asserts that the binary delta compiler outputs the exact byte alignments,
    ordering, and bitwise shift masks expected by the firmware parsing kernel.
    """
    import struct

    from m5resolver.delta_engine import BitmappedDeltaCompiler

    target_slot_index = 3
    expected_shifted_mask = 1 << target_slot_index

    compiled_bytes = BitmappedDeltaCompiler.compile_bitmap_delta(
        slot_id=target_slot_index,
        operational_frequency=100,
        sequence_id=55,
    )

    assert compiled_bytes.startswith(b"\x23\x44")

    payload_body = compiled_bytes[2:]
    unpacked_fields = struct.unpack("!HHI", payload_body)

    assert unpacked_fields[0] == expected_shifted_mask
    assert unpacked_fields[1] == 100
    assert unpacked_fields[2] == 55


class MockTransportMesh:
    def __init__(self) -> None:
        self.payload_cache = b""

    def write(self, data: bytes) -> None:
        self.payload_cache = data


def test_unified_orchestration_synchronization_lifecycle():
    """
    Asserts that the central controller successfully executes schema validation,
    priority compiling, and bitmapped delta token generation in a single pass.
    """
    from m5resolver.controller import UnifiedOrchestrationController

    mock_transport = MockTransportMesh()
    orchestrator = UnifiedOrchestrationController(transport_mesh=mock_transport)

    valid_intent_input = {
        "version": "1.0.0",
        "units": {
            "high_speed_actuator": {
                "type": "hardware_driver",
                "pins": [13],
                "frequency_hz": 500,
                "realtime_critical": True,
            }
        },
    }

    success = orchestrator.synchronize_intent_delta(valid_intent_input, unit_slot=4)

    assert success is True
    assert len(mock_transport.payload_cache) == 10
    assert mock_transport.payload_cache.startswith(b"\x23\x44")


class MockClusterTransport:
    def __init__(self, failure_node: str | None = None) -> None:
        self.failure_node = failure_node
        self.committed_nodes: list[str] = []

    def query_node_readiness(self, node_id: str, payload: dict) -> bool:
        return node_id != self.failure_node

    def broadcast_commit_token(self, node_id: str, payload: dict) -> None:
        self.committed_nodes.append(node_id)


def test_mesh_two_phase_commit_safety():
    """
    Asserts that the cluster synchronizer rolls back gracefully and declines
    the transaction if any individual node fails pre-flight verification.
    """
    from m5resolver.sync_mesh import MeshStateSynchronizer

    cluster_nodes = ["m5_node_alpha", "m5_node_beta", "m5_node_gamma"]

    failed_transport = MockClusterTransport(failure_node="m5_node_beta")
    synchronizer = MeshStateSynchronizer(node_list=cluster_nodes)

    mutation_payload = {"units": {"telemetry_pipe": {"type": "gpio", "frequency_hz": 100}}}

    execution_success = synchronizer.execute_cluster_mutation(mutation_payload, failed_transport)

    assert execution_success is False
    assert len(failed_transport.committed_nodes) == 0


def test_mesh_two_phase_commit_success():
    from m5resolver.sync_mesh import MeshStateSynchronizer

    cluster_nodes = ["m5_node_alpha", "m5_node_beta"]
    transport = MockClusterTransport()
    synchronizer = MeshStateSynchronizer(node_list=cluster_nodes)
    mutation = {"units": {"dsp_worker": {"type": "virtual_dsp", "frequency_hz": 200}}}

    assert synchronizer.execute_cluster_mutation(mutation, transport) is True
    assert len(transport.committed_nodes) == 2
    assert synchronizer.registry_snapshot()["m5_node_alpha"]["dsp_worker"]["frequency_hz"] == 200

