import hashlib
import json

import pytest

from m5resolver.security import intent_content_digest, sign_intent, verify_intent_signature
from m5resolver.validation import IntentValidator, validate_intent_payload


def test_valid_intent_has_no_errors():
    payload = {
        "display": {"text": {"x": 0, "y": 0, "size": 2, "color": 65535, "payload": "ok"}},
        "speaker": {"tone": {"frequency": 440, "duration": 50, "channel": 0}},
        "power": {"led": 10, "off": False},
    }
    assert validate_intent_payload(payload) == []


def test_invalid_intent_reports_errors():
    payload = {
        "invalid": True,
        "display": {"text": {"x": "left", "payload": 123}},
        "speaker": {"tone": {"frequency": "high"}},
    }
    errors = validate_intent_payload(payload)
    assert any("unsupported top-level key: invalid" in e for e in errors)
    assert any("display.text.x must be an integer" in e for e in errors)
    assert any("display.text.payload must be a string" in e for e in errors)
    assert any("speaker.tone.frequency must be a number" in e for e in errors)


def test_secure_host_signature_enforcement():
    """
    Asserts that the intent orchestration pipelines successfully demand and evaluate
    cryptographic hash fields to maintain cluster integrity barriers.
    """
    validator = IntentValidator()

    secure_payload = {
        "version": "23.0.0",
        "intent": {
            "action": "reallocate_resources",
            "target": "mesh_node_0",
        },
        "security": {
            "signature_hex": "8f43c0a2e15c4493aaef",
            "timestamp_epoch": 1779874800,
        },
    }

    assert validator is not None
    payload_string = json.dumps(secure_payload, sort_keys=True)
    computed_hash = hashlib.sha256(payload_string.encode("utf-8")).hexdigest()
    assert len(computed_hash) == 64

    signed = sign_intent({"display": {"clear": True}})
    assert verify_intent_signature(signed) == []
    assert validate_intent_payload(signed) == []

    tampered = dict(signed)
    tampered["display"] = {"clear": False}
    assert any("mismatch" in e for e in verify_intent_signature(tampered))


def test_corrupted_signature_rejected():
    intent = sign_intent({"power": {"led": 32}})
    intent["security"]["signature_hex"] = "deadbeef"
    errors = validate_intent_payload(intent)
    assert any("mismatch" in e for e in errors)


def test_registry_requires_signature_in_secure_mode():
    payload = {"registry": {"units": {"heartbeat": {"frequency_hz": 2}}}}
    assert validate_intent_payload(payload) == []
    errors = validate_intent_payload(payload, require_registry_signature=True)
    assert any("require security.signature_hex" in e for e in errors)

    signed = sign_intent(payload)
    assert validate_intent_payload(signed, require_registry_signature=True) == []


def test_binary_jit_allocation_constraints():
    """
    Asserts that the schema checking subsystems cap raw injected binary sizes
    to prevent memory exhaustion or stack overflows in the IRAM allocation blocks.
    """
    validator = IntentValidator()

    oversized_jit_payload = {
        "units": {
            "custom_asm_routine": {
                "type": "native_jit_patch",
                "code_size_bytes": 8192,
                "payload_hex": "4f555246" * 2048,
            }
        }
    }

    assert validator is not None
    errors = validate_intent_payload(oversized_jit_payload)
    assert any("exceeds safe IRAM limit" in e for e in errors)


def test_instruction_ram_allocation_constraints():
    """
    Asserts that the binary compiler bounds payloads appropriately to
    prevent memory safety violations inside the firmware instruction spaces.
    """
    from m5resolver.jit_compiler import MAX_JIT_CODE_BYTES, verify_iram_payload_safe

    max_permissible_iram_bytes = MAX_JIT_CODE_BYTES
    simulated_oversized_code_size = 8192

    assert verify_iram_payload_safe(simulated_oversized_code_size) is False
    assert verify_iram_payload_safe(max_permissible_iram_bytes) is True
    assert verify_iram_payload_safe(4) is True
    assert verify_iram_payload_safe(0) is False


def test_valid_native_jit_intent_passes():
    payload = {
        "native_jit": {
            "unit_id": "custom_asm_routine",
            "type": "native_jit_patch",
            "code_size_bytes": 4,
            "payload_hex": "4f555246",
            "execute": True,
        }
    }
    assert validate_intent_payload(payload) == []


def test_native_jit_size_mismatch_rejected():
    payload = {
        "native_jit": {
            "type": "native_jit_patch",
            "code_size_bytes": 99,
            "payload_hex": "deadbeef",
        }
    }
    errors = validate_intent_payload(payload)
    assert any("does not match payload_hex length" in e for e in errors)


def test_prevent_cyclic_dependency_faults():
    """
    Asserts that the graph infrastructure blocks structural execution plans
    containing cyclic paths, keeping the network free from infinite resolution loops.
    """
    from m5resolver.graph_engine import StateGraphEngine

    graph = StateGraphEngine()
    graph.add_reactive_unit("node_alpha", {"type": "virtual"}, depends_on=["node_beta"])
    graph.add_reactive_unit("node_beta", {"type": "virtual"}, depends_on=["node_alpha"])

    assert "node_alpha" in graph.nodes
    assert "node_beta" in graph.nodes["node_alpha"].dependencies
    assert graph.has_cycle() is True
    assert any("cyclic dependency" in err for err in graph.validate_dag())


def test_registry_intent_with_cycle_rejected():
    payload = {
        "registry": {
            "units": {
                "node_alpha": {"bus": "virtual", "capabilities": [], "depends_on": ["node_beta"]},
                "node_beta": {"bus": "virtual", "capabilities": [], "depends_on": ["node_alpha"]},
            }
        }
    }
    errors = validate_intent_payload(payload)
    assert any("cyclic dependency" in e for e in errors)


def test_instruction_address_boundary_fences():
    """
    Asserts that memory overlay structures target memory spaces exclusively
    within permitted execution address blocks, preventing hardware boundary infractions.
    """
    from m5resolver.memory_compiler import (
        HardwareMemoryCompiler,
        IRAM_EXEC_END,
        IRAM_EXEC_START,
    )

    invalid_address_pointer = 0x3FF00000
    instruction_payload_bytes = b"\x00\x00\x00\x00"

    assert HardwareMemoryCompiler.verify_address_safety(invalid_address_pointer) is False
    assert HardwareMemoryCompiler.verify_address_safety(IRAM_EXEC_START) is True
    assert HardwareMemoryCompiler.verify_address_safety(IRAM_EXEC_END) is True

    with pytest.raises(ValueError, match="outside IRAM fence"):
        HardwareMemoryCompiler.compile_memory_overlay(
            invalid_address_pointer, instruction_payload_bytes
        )


def test_automated_priority_elevation_contracts():
    """
    Asserts that the configuration compiler accurately flags resource conflicts
    and injects high-priority execution tiers to protect shared peripherals.
    """
    from m5resolver.scheduler_compiler import HostSchedulerCompiler

    contested_intent_block = {
        "units": {
            "high_speed_spi_bus": {"pins": [18, 23], "realtime_critical": True},
            "ambient_logger": {"pins": [18], "realtime_critical": False},
        }
    }

    compiled_output = HostSchedulerCompiler.compute_priority_matrix(contested_intent_block)

    assert compiled_output["units"]["high_speed_spi_bus"]["assigned_priority_tier"] == 3
    assert compiled_output["units"]["ambient_logger"]["assigned_priority_tier"] == 3


def test_predictive_priority_inheritance_contracts():
    """
    Asserts that the scheduler compiler successfully identifies shared peripheral
    contentions and escalates scheduling tiers to safeguard critical real-time execution.
    """
    from m5resolver.scheduler_compiler import HostSchedulerCompiler

    contested_payload = {
        "units": {
            "critical_motor_task": {"pins": [18, 23], "realtime_critical": True},
            "low_priority_telemetry": {"pins": [18], "realtime_critical": False},
        }
    }

    optimized_output = HostSchedulerCompiler.compute_priority_matrix(contested_payload)

    assert optimized_output["units"]["critical_motor_task"]["assigned_priority_tier"] == 3
    assert optimized_output["units"]["low_priority_telemetry"]["assigned_priority_tier"] == 3


def test_predictive_scheduling_audit_collects_escalations():
    from m5resolver.scheduler_compiler import HostSchedulerCompiler

    intent = {
        "registry": {
            "units": {
                "critical_motor_task": {"pins": [18], "realtime_critical": True},
                "low_priority_telemetry": {"pins": [18]},
            }
        }
    }
    compiled, audit = HostSchedulerCompiler.compile_with_audit(intent)
    assert compiled["registry"]["units"]["critical_motor_task"]["assigned_priority_tier"] == 3
    assert any("tier=3" in e or "critical_motor_task" in e for e in audit.escalations)


def test_invalid_priority_tier_rejected():
    payload = {
        "registry": {
            "units": {
                "motor": {"assigned_priority_tier": 9, "pins": [12]},
            }
        }
    }
    errors = validate_intent_payload(payload)
    assert any("assigned_priority_tier" in e for e in errors)


def test_autonomous_healing_remediation_generation():
    """
    Asserts that the mitigation agent correctly captures degraded device metrics
    and generates an appropriate binary fast-path throttling override token.
    """
    from m5resolver.controller import AutonomousMitigationEngine

    mitigator = AutonomousMitigationEngine(None)

    degraded_device_packet = {
        "version": "1.0.0",
        "type": "telemetry",
        "unit_id": 7,
        "active_pin": 10,
        "metrics": {
            "free_heap": 18000,
            "task_jitter_ms": 65,
        },
    }

    raw_packet_string = json.dumps(degraded_device_packet)

    remediation_token = mitigator.inspect_telemetry_and_heal(raw_packet_string)

    assert len(remediation_token) == 10
    assert remediation_token.startswith(b"\x23\x23")


def test_autonomous_healing_skips_healthy_telemetry():
    from m5resolver.controller import AutonomousMitigationEngine

    mitigator = AutonomousMitigationEngine(None)
    healthy = {
        "type": "telemetry",
        "metrics": {"free_heap": 48000, "task_jitter_ms": 5},
    }
    assert mitigator.inspect_telemetry_and_heal(healthy) == b""


def test_branch_flatten_packing_contracts():
    """
    Asserts that the branch compiler accurately flattens conditional logic
    and outputs the exact structural byte alignment required by the jump microkernel.
    """
    import struct

    from m5resolver.branch_flatten import BranchFlattenCompiler

    target_condition = 4
    target_function_slot = 12
    priority_mask_tier = 3

    compiled_bytes = BranchFlattenCompiler.compile_jump_vector(
        condition_id=target_condition,
        target_function_slot=target_function_slot,
        execution_tier=priority_mask_tier,
    )

    assert compiled_bytes.startswith(b"\x23\x46")

    payload_body = compiled_bytes[2:]
    unpacked_fields = struct.unpack("!BBH", payload_body)

    assert unpacked_fields[0] == target_condition
    assert unpacked_fields[1] == target_function_slot
    assert unpacked_fields[2] == priority_mask_tier


def test_interrupt_vector_packing_contracts():
    """
    Asserts that the vector compiler accurately aligns metadata fields and
    outputs the precise byte configurations required by the firmware IRAM fence.
    """
    import struct

    from m5resolver.vector_compiler import HostVectorCompiler

    target_interrupt_channel = 2
    simulated_code_length = 128
    tracking_transaction_id = 999

    compiled_bytes = HostVectorCompiler.compile_vector_overlay(
        interrupt_source_id=target_interrupt_channel,
        byte_length=simulated_code_length,
        transaction_id=tracking_transaction_id,
    )

    assert compiled_bytes.startswith(b"\x23\x49")

    payload_body = compiled_bytes[2:]
    unpacked_fields = struct.unpack("!BHI", payload_body)

    assert unpacked_fields[0] == target_interrupt_channel
    assert unpacked_fields[1] == simulated_code_length
    assert unpacked_fields[2] == tracking_transaction_id


def test_closed_loop_remediation_packing_contracts():
    """
    Asserts that the remediation engine correctly traps degraded hardware profiles
    and structures the exact fallback byte fields expected by the firmware intercept gates.
    """
    import struct

    from m5resolver.remediation import AutonomousRemediationEngine

    target_unit = 7
    hazardous_heap_level = 16000
    hazardous_jitter_level = 55

    remediation_token, was_repaired = AutonomousRemediationEngine().inspect_and_heal_profile(
        unit_id=target_unit,
        free_heap_bytes=hazardous_heap_level,
        task_jitter_ms=hazardous_jitter_level,
    )

    assert was_repaired is True
    assert remediation_token.startswith(b"\x23\x52")

    payload_body = remediation_token[2:]
    unpacked_fields = struct.unpack("!BBH", payload_body)

    assert unpacked_fields[0] == target_unit
    assert unpacked_fields[1] == 0
    assert unpacked_fields[2] == 10


def test_visualizer_data_ingestion_bounds(capsys):
    """
    Asserts that the diagnostic visualizer correctly handles missing or zeroed
    telemetry parameters gracefully without throwing runtime execution faults.
    """
    from m5resolver.dashboard import TerminalStateVisualizer

    malformed_snapshot = {
        "active_unit": None,
        "free_heap_bytes": 0,
    }

    TerminalStateVisualizer.render_system_matrix(malformed_snapshot, clear_screen=False)
    captured = capsys.readouterr()
    assert "m5-utah // REAL-TIME PHYSICAL REGISTER" in captured.out
    assert "Slot ID N/A" in captured.out
    assert "Typestate Sequence   : IDLE" in captured.out


def test_secure_monotonic_sequence_contracts():
    """
    Asserts that the security wire compiler increments transactional index pools
    linearly and generates precise byte maps to feed the firmware security fence.
    """
    from m5resolver.secure_wire import SecureWireEncoder

    encoder = SecureWireEncoder(initial_sequence_id=5000)

    frame_alpha = encoder.secure_pack_frame(target_unit_id=1, functional_opcode=4, data_vector=100)
    frame_beta = encoder.secure_pack_frame(target_unit_id=1, functional_opcode=4, data_vector=100)

    seq_alpha = SecureWireEncoder.unpack_secure_frame(frame_alpha)[3]
    seq_beta = SecureWireEncoder.unpack_secure_frame(frame_beta)[3]

    assert seq_alpha == 5000
    assert seq_beta == 5001
    assert seq_beta > seq_alpha
