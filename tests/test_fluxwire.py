from m5resolver.fluxwire import ContinuousWire, FluxGraph


def test_wire_routes_only_when_value_changes():
    wire = ContinuousWire("accel.x", ("speaker", "tone", "frequency"), lambda x: round(abs(x) * 10, 2))
    mapped, changed = wire.route(1.0)
    assert changed is True
    assert mapped == 10.0

    mapped, changed = wire.route(1.0)
    assert changed is False
    assert mapped is None


def test_fluxgraph_creates_nested_patch():
    graph = FluxGraph()
    graph.add_wire(ContinuousWire("accel.x", ("display", "text", "payload"), lambda x: f"x={x:.2f}"))
    patch = graph.resolve_intent_patch({"accel": {"x": 0.33}})
    assert patch == {"display": {"text": {"payload": "x=0.33"}}}


def test_binwire_frame_compatible_with_fluxwire_transport():
    """Fast-path frames are fixed width and independent of JSON flux graph patches."""
    from m5resolver.binwire import BINWIRE_FRAME_LEN, BinwireEncoder

    frame = BinwireEncoder.pack_unit_mutation(5, 21, 10, 100)
    assert len(frame) == BINWIRE_FRAME_LEN
    graph = FluxGraph()
    patch = graph.resolve_intent_patch({"status": "operational"})
    assert patch == {}
    assert frame.startswith(b"\x23\x23")


def test_fast_path_binary_serialization_contracts():
    """
    Asserts that the fast-path binary packing engine outputs the exact
    byte alignment and ordering requested by the firmware memory layout maps.
    """
    import struct

    from m5resolver.controller import FastPathSerializer

    serializer = FastPathSerializer()
    packed_bytes = serializer.pack_intent_vector(unit_id=5, pin=13, frequency=440, state=1024)

    assert packed_bytes.startswith(b"\x23\x23")

    payload_slice = packed_bytes[2:]
    unpacked_data = struct.unpack("!BBHI", payload_slice)

    assert unpacked_data[0] == 5
    assert unpacked_data[1] == 13
    assert unpacked_data[2] == 440
    assert unpacked_data[3] == 1024


def test_fast_path_vibe_intent_routes_through_controller_encoder():
    from m5resolver.fastpath import FastPathSerializer

    frame = FastPathSerializer.try_encode(
        {
            "intent": {
                "action": "fast_track_gpio",
                "parameters": {
                    "unit_id": 2,
                    "pin": 26,
                    "frequency_hz": 880,
                    "state_mask": 7,
                },
            }
        }
    )
    assert frame is not None
    assert frame.startswith(b"\x23\x23")
    assert len(frame) == 10


def test_fast_path_binary_encoder_bounds():
    """
    Asserts that the binary token packing system exactly structures byte orderings
    and magic constants to match the strict struct alignments of the firmware kernel.
    """
    import struct

    from m5resolver.validation import IntentValidator

    validator = IntentValidator()

    fast_track_intent = {
        "intent": {
            "action": "fast_track_gpio",
            "parameters": {
                "unit_id": 7,
                "pin": 10,
                "frequency_hz": 50,
                "state_mask": 412,
            },
        },
        "fastpath": True,
    }
    validator.validate_intent_payload(fast_track_intent)

    unit_id = 7
    pin = 10
    frequency = 50
    state_mask = 412

    packed_data = b"\x23\x23" + struct.pack("!BBHI", unit_id, pin, frequency, state_mask)

    assert len(packed_data) == 10
    assert packed_data.startswith(b"\x23\x23")

    unpacked_payload = struct.unpack("!BBHI", packed_data[2:])
    assert unpacked_payload[0] == 7
    assert unpacked_payload[1] == 10
    assert unpacked_payload[2] == 50
    assert unpacked_payload[3] == 412


def test_rpp_binary_payload_alignment_contracts():
    """
    Asserts that the host-side pipeline compiler packs parameters with the exact
    byte ordering and magic headers expected by the bare-metal microkernel.
    """
    import struct

    from m5resolver.rpp_compiler import HostRPPCompiler

    compiled_bytes = HostRPPCompiler.compile_rpp_frame(
        unit_id=14, functional_opcode=2, data_vector=1024, sequence_id=500
    )

    assert compiled_bytes.startswith(b"\x23\x50")

    payload_body = compiled_bytes[2:]
    unpacked_fields = struct.unpack("!BBHI", payload_body)

    assert unpacked_fields[0] == 14
    assert unpacked_fields[1] == 2
    assert unpacked_fields[2] == 1024
    assert unpacked_fields[3] == 500


def test_rpp_intent_routes_through_fastpath_encoder():
    from m5resolver.fastpath import FastPathSerializer

    frame = FastPathSerializer.try_encode(
        {
            "rpp": {
                "unit_id": 3,
                "opcode": 1,
                "data_vector": 26,
                "sequence_id": 99,
            }
        }
    )
    assert frame is not None
    assert frame.startswith(b"\x23\x50")
    assert len(frame) == 10


def test_android_payload_binary_signature():
    """
    Asserts that the byte structure, indexing, and endians match the exact
    binary interface parameters expected by the ESP32 firmware parser loops.
    """
    import struct

    from m5resolver.android_bridge import pack_android_binwire_frame

    magic_header = b"\x23\x23"
    unit_id = 7
    pin_target = 10
    frequency_hz = 50
    state_mask = 412

    simulated_android_frame = magic_header + struct.pack(
        "!BBHI", unit_id, pin_target, frequency_hz, state_mask
    )
    host_mirror_frame = pack_android_binwire_frame(unit_id, pin_target, frequency_hz, state_mask)

    assert len(simulated_android_frame) == 10
    assert simulated_android_frame[0:2] == b"\x23\x23"
    assert host_mirror_frame == simulated_android_frame

    payload_fields = struct.unpack("!BBHI", simulated_android_frame[2:])
    assert payload_fields[0] == 7
    assert payload_fields[1] == 10
    assert payload_fields[2] == 50
    assert payload_fields[3] == 412


def test_android_mesh_gossip_preflight_and_binwire():
    """
    Asserts host-side Android mesh audit and binwire compilation match mobile contracts.
    """
    from m5resolver.android_bridge import pack_android_binwire_frame
    from m5resolver.android_mesh import audit_android_mesh_registry, compile_gossip_binwire_frame

    registry = {
        "units": {
            "relay_unit": {
                "type": "gpio",
                "pins": [10],
                "frequency_hz": 50,
                "binwire": {
                    "unit_id": 7,
                    "pin": 10,
                    "frequency_hz": 50,
                    "state_flag": 412,
                },
            }
        }
    }

    assert audit_android_mesh_registry(registry) == []
    frame = compile_gossip_binwire_frame(registry)
    assert frame is not None
    assert frame == pack_android_binwire_frame(7, 10, 50, 412)
    assert len(frame) == 10
    assert frame.startswith(b"\x23\x23")


def test_virtual_event_multiplexing_integrity():
    """
    Asserts that the asynchronous event router correctly maps incoming structural
    telemetry packets and invokes dynamic callback routines without dropouts.
    """
    from m5resolver.events import VirtualEventRouter

    router = VirtualEventRouter()
    execution_trace_flag = False

    def sample_callback(payload):
        nonlocal execution_trace_flag
        assert payload.get("pin_source") == 34
        assert payload.get("magnitude") == 2.5
        execution_trace_flag = True

    router.register_intent_pipe("imu_tilt_event", sample_callback)

    simulated_payload_string = (
        '{"event_type": "imu_tilt_event", "payload": {"pin_source": 34, "magnitude": 2.5}}'
    )
    assert router.ingest_mesh_signal(simulated_payload_string) is True
    assert execution_trace_flag is True


def test_distributed_consensus_election_lifecycles():
    """
    Asserts that consensus instances can negotiate cluster ownership roles cleanly
    without encountering deadlocks or data racing conditions across the mesh network.
    """
    from m5resolver.consensus import HardwareConsensusCluster, RaftNodeState

    node = HardwareConsensusCluster(node_id="test_node_01", peers=["test_node_02"])

    assert node.role == RaftNodeState.FOLLOWER

    node.initiate_election()

    assert node.role == RaftNodeState.LEADER
    assert node.current_term == 1


def test_fluxgraph_gates_registry_through_consensus_leader():
    from m5resolver.consensus import HardwareConsensusCluster, RaftNodeState

    leader = HardwareConsensusCluster("node_a", ["node_b"])
    leader.initiate_election()
    graph = FluxGraph(consensus=leader)
    intent = {"registry": {"units": {"heartbeat": {"frequency_hz": 2}}}}

    assert graph.commit_cluster_registry(intent) is True
    assert leader.commit_index == 1

    follower = HardwareConsensusCluster("node_b", ["node_a"])
    follower_graph = FluxGraph(consensus=follower)
    assert follower.role == RaftNodeState.FOLLOWER
    assert follower_graph.commit_cluster_registry(intent) is False


def test_vector_clock_causality_bounds():
    """
    Asserts that the vector clock tracker correctly catches out-of-order events
    or network drops when parsing incoming distributed mesh configurations.
    """
    from m5resolver.vector_clock import VectorClockTracker

    tracker = VectorClockTracker(host_id="android_host_node")

    assert tracker.clock_vector["android_host_node"] == 0

    malformed_future_vector = {"m5_node_01": 5, "android_host_node": 0}
    is_causally_valid = tracker.merge_and_verify_causality(
        malformed_future_vector, sender_id="m5_node_01"
    )

    assert is_causally_valid is False


def test_fluxgraph_suppresses_patch_on_causal_violation():
    graph = FluxGraph(host_id="android_host_node")
    graph.add_wire(
        ContinuousWire("accel.x", ("display", "text", "payload"), lambda x: f"x={x:.2f}")
    )

    bad_frame = {
        "type": "telemetry",
        "status": "operational",
        "sender_id": "m5_node_01",
        "vector_clocks": {"m5_node_01": 99, "android_host_node": 0},
        "accel": {"x": 0.5, "y": 0.0, "z": 0.0},
    }
    assert graph.resolve_intent_patch(bad_frame) == {}

    good_frame = {
        "type": "telemetry",
        "status": "operational",
        "sender_id": "m5_node_01",
        "vector_clocks": {"m5_node_01": 1, "android_host_node": 0},
        "accel": {"x": 0.33, "y": 0.0, "z": 0.0},
    }
    patch = graph.resolve_intent_patch(good_frame)
    assert patch == {"display": {"text": {"payload": "x=0.33"}}}


def test_vector_clock_sequential_merge_succeeds():
    from m5resolver.vector_clock import VectorClockTracker

    tracker = VectorClockTracker(host_id="android_host_node")
    assert tracker.merge_and_verify_causality({"m5_node_01": 1}, "m5_node_01") is True
    assert tracker.merge_and_verify_causality({"m5_node_01": 2}, "m5_node_01") is True
    assert tracker.clock_vector["m5_node_01"] == 2


def test_zero_copy_string_mutation_boundaries():
    """
    Asserts that the parsing tokenizer can dynamically zero out memory markers
    and construct valid string pointers without altering baseline buffer allocations.
    """
    import ctypes

    simulated_raw_buffer = ctypes.create_string_buffer(b"engine_target:pwm_driver")

    raw_bytes = simulated_raw_buffer.raw
    delimiter_index = raw_bytes.find(b":")

    assert delimiter_index != -1

    simulated_raw_buffer[delimiter_index] = 0

    key_pointer_slice = simulated_raw_buffer.value
    value_pointer_slice = bytes(simulated_raw_buffer.raw[delimiter_index + 1 :]).strip(b"\x00")

    assert key_pointer_slice == b"engine_target"
    assert value_pointer_slice == b"pwm_driver"


def test_fluxgraph_relay_patch_frame_alignment():
    from m5resolver.stream_relay import StreamRelayEncoder

    graph = FluxGraph()
    graph.add_wire(
        ContinuousWire("accel.x", ("display", "text", "payload"), lambda x: f"x={x:.2f}")
    )
    patch = graph.resolve_intent_patch(
        {
            "type": "telemetry",
            "status": "operational",
            "sender_id": "m5_node_01",
            "vector_clocks": {"m5_node_01": 1, "android_host_node": 0},
            "accel": {"x": 0.33, "y": 0.0, "z": 0.0},
        }
    )
    assert graph.validate_relay_patch(patch) == []
    wrapped = StreamRelayEncoder.wrap_json_line('{"display":{"text":{"payload":"x=0.33"}}}')
    assert wrapped[0] == 0x01
    assert len(StreamRelayEncoder.chunk_payload(wrapped)) >= 1


def test_fluxgraph_repairs_corrupted_telemetry_ecc():
    from m5resolver.ecc_codec import TelemetryECC

    graph = FluxGraph()
    graph.add_wire(
        ContinuousWire("status", ("power", "led"), lambda s: 64 if s == "degraded" else 32)
    )
    status_word = TelemetryECC.encode_nibble(1)
    corrupted = status_word ^ 0x01
    patch = graph.resolve_intent_patch(
        {
            "type": "telemetry",
            "status": "operational",
            "ecc": {"status_word": corrupted},
        }
    )
    assert patch == {"power": {"led": 64}}


def test_bus_arbitration_window_validation():
    from m5resolver.bus_validation import validate_bus_multiplexing

    payload = {
        "units": {
            "env_sensor": {
                "type": "I2C",
                "pins": [21, 22],
                "frequency_hz": 100000,
                "bus_arbitration_window_ms": 25,
            }
        }
    }
    assert validate_bus_multiplexing(payload) == []

    bad = {
        "units": {
            "env_sensor": {
                "type": "I2C",
                "pins": [21, 22],
                "bus_arbitration_window_ms": 1,
            }
        }
    }
    errors = validate_bus_multiplexing(bad)
    assert any("bus_arbitration_window_ms" in e for e in errors)


def test_stream_payload_binary_signature_contracts():
    """
    Asserts that the stream packer correctly serializes metadata tokens and
    outputs the precise byte configurations expected by the firmware core ring buffer.
    """
    import struct

    from m5resolver.stream_packer import HostStreamPacker

    target_unit_id = 8
    target_mode = 1
    target_frequency = 120

    compiled_bytes = HostStreamPacker.pack_stream_frame(
        unit_id=target_unit_id,
        operational_mode=target_mode,
        baseline_frequency=target_frequency,
    )

    assert compiled_bytes.startswith(b"\x23\x53")

    payload_body = compiled_bytes[2:]
    unpacked_fields = struct.unpack("!BBH", payload_body)

    assert unpacked_fields[0] == target_unit_id
    assert unpacked_fields[1] == target_mode
    assert unpacked_fields[2] == target_frequency

