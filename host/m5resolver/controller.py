from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

import serial

from .agent import AgenticController, DeviceState
from .binwire import BINWIRE_FRAME_LEN, BinwireEncoder
from .consensus import HardwareConsensusCluster, RaftNodeState
from .branch_flatten import FLATTEN_FRAME_LEN, BranchFlattenCompiler
from .vector_compiler import (
    MAX_VECTOR_PATCH_BYTES,
    HostVectorCompiler,
)
from .delta_engine import BITMAP_DELTA_MAGIC, BITMAP_DELTA_FRAME_LEN, BitmappedDeltaCompiler, DeltaEncoder
from .events import VIRTUAL_EVENT_STREAM_PREFIX, VirtualEventRouter
from .graph_engine import StateGraphEngine
from .memory_compiler import (
    IRAM_EXEC_END,
    IRAM_EXEC_START,
    HardwareMemoryCompiler,
    MAX_OVERLAY_PAYLOAD,
    OVERLAY_MAGIC,
)
from .fastpath import FastPathSerializer
from .rpp_compiler import RPP_FRAME_LEN, HostRPPCompiler
from .fluxwire import FluxGraph
from .jit_compiler import HostJitCompiler
from .memory_profiler import DEFAULT_HANDLE_POOL_BYTES, HostMemoryProfiler
from .resource_orchestrator import HostResourceOrchestrator, ResourcePressureLevel
from .remediation import (
    HEALTH_VITALS_STREAM_PREFIX,
    REMEDIATION_FRAME_LEN,
    AutonomousRemediationEngine,
)
from .mitigation_engine import (
    TELEMETRY_STREAM_PREFIX,
    AutonomousMitigationEngine,
    MitigationStats,
)
from .optimizer import HardwareCostModel
from .replay_engine import HostReplayEngine, ReplayResult, TIME_TRAVEL_PREFIX
from .scheduler_compiler import HostSchedulerCompiler
from .security import sign_intent
from .sync_mesh import ControllerClusterTransport, MeshStateSynchronizer
from .stream_packer import STREAM_FRAME_LEN, STREAM_MAGIC, HostStreamPacker
from .stream_relay import StreamRelayEncoder
from .validation import IntentValidator, validate_intent_payload
from .typestate import SystemTypestateEnforcer
from .dashboard import TerminalStateVisualizer
from .secure_wire import SECURE_WIRE_FRAME_LEN, SecureWireEncoder


logger = logging.getLogger("m5resolver.controller")


@dataclass
class TelemetryFrame:
    payload: dict[str, Any]
    raw: str


@dataclass
class TimeTravelFrame:
    payload: dict[str, Any]
    raw: str
    replay: ReplayResult


class IntentController:
    """Bidirectional serial bridge with in-memory device state and agent loop."""

    def __init__(
        self,
        port: str,
        baud: int = 115200,
        timeout: float = 0.2,
        *,
        registry_path: str | Path | None = None,
        telemetry_schema_path: str | Path | None = None,
        enable_agent: bool = True,
        enable_time_travel: bool = True,
        enable_consensus: bool = False,
        node_id: str | None = None,
        consensus_peers: list[str] | None = None,
        sign_intents: bool = False,
        require_registry_signature: bool = False,
        enable_resource_pruning: bool = True,
        enable_memory_profiling: bool = True,
        enable_scheduler_compilation: bool = True,
        enable_resource_orchestration: bool = True,
        enable_autonomous_mitigation: bool = True,
        enable_autonomous_remediation: bool = True,
        enable_typestate_enforcement: bool = True,
        enable_dashboard: bool = False,
        enable_secure_wire: bool = True,
        default_available_heap: int = 32_000,
        handle_pool_limit_bytes: int = DEFAULT_HANDLE_POOL_BYTES,
        on_replay_fault: Callable[[ReplayResult], None] | None = None,
    ) -> None:
        self.port = port
        self.baud = baud
        self.timeout = timeout
        self._link: serial.Serial | None = None
        self.device_state = DeviceState()
        self.consensus: HardwareConsensusCluster | None = None
        if enable_consensus and node_id:
            self.consensus = HardwareConsensusCluster(node_id, consensus_peers or [])
        host_id = node_id or "android_host_node"
        self.flux = FluxGraph(consensus=self.consensus, host_id=host_id)
        mesh_nodes = [host_id]
        if consensus_peers:
            mesh_nodes.extend(consensus_peers)
        self.mesh_synchronizer = MeshStateSynchronizer(mesh_nodes)
        self._agent: AgenticController | None = None
        self._replay_engine: HostReplayEngine | None = None
        self._on_replay_fault = on_replay_fault
        self._sign_intents = sign_intents
        self._require_registry_signature = require_registry_signature
        self._enable_resource_pruning = enable_resource_pruning
        self._enable_memory_profiling = enable_memory_profiling
        self._enable_scheduler_compilation = enable_scheduler_compilation
        self._enable_resource_orchestration = enable_resource_orchestration
        self._enable_autonomous_mitigation = enable_autonomous_mitigation
        self._enable_autonomous_remediation = enable_autonomous_remediation
        self._enable_typestate_enforcement = enable_typestate_enforcement
        self._enable_dashboard = enable_dashboard
        self._enable_secure_wire = enable_secure_wire
        self._default_available_heap = default_available_heap
        self.typestate_enforcer = SystemTypestateEnforcer()
        self.secure_wire = SecureWireEncoder()
        self._dashboard_typestate = "IDLE"
        self.mitigation_engine: AutonomousMitigationEngine | None = None
        self.remediation_engine: AutonomousRemediationEngine | None = None
        self.memory_profiler = HostMemoryProfiler(memory_pool_limit_bytes=handle_pool_limit_bytes)
        self.resource_orchestrator = HostResourceOrchestrator()
        self.last_replay: ReplayResult | None = None
        self.event_router = VirtualEventRouter()
        self.event_router.set_intent_sink(self._on_event_intent)
        self.event_router.bind_default_routes()
        if enable_time_travel:
            schema = telemetry_schema_path or "schemas/telemetry.schema.json"
            self._replay_engine = HostReplayEngine(telemetry_schema_path=schema)
        if enable_agent and registry_path:
            self._agent = AgenticController(
                registry_path=registry_path,
                telemetry_schema_path=telemetry_schema_path,
                on_corrective_intent=self._on_corrective_intent,
            )

    def attach_mitigation_engine(self) -> None:
        if self._enable_autonomous_mitigation:
            self.mitigation_engine = AutonomousMitigationEngine(self)

    def attach_remediation_engine(self) -> None:
        if self._enable_autonomous_remediation:
            self.remediation_engine = AutonomousRemediationEngine()

    def _on_corrective_intent(self, intent: dict[str, Any]) -> None:
        if self.is_open:
            self.send_intent(intent)

    def _on_event_intent(self, intent: dict[str, Any]) -> None:
        if self.is_open:
            self.send_intent(intent, stage=False)

    def open(self) -> None:
        self._link = serial.Serial(self.port, self.baud, timeout=self.timeout)
        time.sleep(1.25)
        self.attach_mitigation_engine()
        self.attach_remediation_engine()

    def close(self) -> None:
        if self._link and self._link.is_open:
            self._link.close()
        self._link = None

    @property
    def is_open(self) -> bool:
        return self._link is not None and self._link.is_open

    def available_heap_bytes(self) -> int:
        metrics = self.device_state.last_telemetry.get("metrics", {})
        free_heap = metrics.get("free_heap")
        if isinstance(free_heap, int) and free_heap > 0:
            return free_heap
        return self._default_available_heap

    def prune_intent_for_device(self, intent: dict[str, Any]) -> tuple[dict[str, Any], bool]:
        if not self._enable_resource_pruning:
            return intent, False
        return HardwareCostModel.prune_intent(intent, self.available_heap_bytes())

    def _collect_registry_units(self, intent: dict[str, Any]) -> dict[str, dict[str, Any]]:
        registry = intent.get("registry")
        if not isinstance(registry, dict):
            return {}
        units = registry.get("units")
        if isinstance(units, dict):
            return {k: v for k, v in units.items() if isinstance(v, dict)}
        if isinstance(units, list):
            return {
                str(record["unit_id"]): record
                for record in units
                if isinstance(record, dict) and "unit_id" in record
            }
        return {}

    def preflight_memory_for_intent(self, intent: dict[str, Any]) -> list[str]:
        if not self._enable_memory_profiling:
            return []
        units = self._collect_registry_units(intent)
        if not units:
            top_level = intent.get("units")
            if isinstance(top_level, dict):
                units = {k: v for k, v in top_level.items() if isinstance(v, dict)}
        if not units:
            return []
        return self.memory_profiler.evaluate_registry_units(units)

    def send_memory_compact(self) -> list[str]:
        """Request firmware handle-pool compaction before large registry pushes."""
        intent = self.memory_profiler.compaction_intent()
        if not self.is_open or self._link is None:
            raise RuntimeError("Serial link is not open")
        payload = json.dumps(intent, separators=(",", ":")) + "\n"
        self._link.write(payload.encode("utf-8"))
        self._link.flush()
        self.memory_profiler.estimated_pool_top = 0
        return []

    def send_intent(
        self, intent: dict[str, Any], *, stage: bool = True, sign: bool | None = None
    ) -> list[str]:
        if self._enable_scheduler_compilation:
            intent, scheduling_audit = HostSchedulerCompiler.compile_with_audit(intent)
            for escalation in scheduling_audit.escalations:
                logger.info("[SCHEDULER AUDIT] %s", escalation)
            for warning in scheduling_audit.warnings:
                logger.warning("[SCHEDULER AUDIT] %s", warning)

        if self._enable_typestate_enforcement:
            typestate_errors = self.typestate_enforcer.validate_intent_typestate(intent)
            if typestate_errors:
                return typestate_errors
            typestate_block = intent.get("typestate")
            if isinstance(typestate_block, dict) and "target" in typestate_block:
                self._dashboard_typestate = str(typestate_block["target"]).upper()

        if self._enable_resource_orchestration:
            orchestrator_errors = self.resource_orchestrator.preflight_transmit(
                intent, free_heap=self.available_heap_bytes()
            )
            if orchestrator_errors:
                return orchestrator_errors

        memory_errors = self.preflight_memory_for_intent(intent)
        if memory_errors and self._enable_memory_profiling:
            if self.is_open:
                logger.warning(
                    "[PROFILER] Memory preflight failed — issuing compaction before retry"
                )
                compact_errors = self.send_memory_compact()
                if compact_errors:
                    return memory_errors + compact_errors
                retry_errors = self.preflight_memory_for_intent(intent)
                if retry_errors:
                    return retry_errors
            else:
                return memory_errors

        intent, was_pruned = self.prune_intent_for_device(intent)
        if was_pruned:
            logger.info(
                "[PRUNER] Intent downsized for %s bytes free heap before transmit",
                self.available_heap_bytes(),
            )

        should_sign = self._sign_intents if sign is None else sign
        if should_sign:
            intent = sign_intent(intent)

        preflight = validate_intent_payload(
            intent, require_registry_signature=self._require_registry_signature
        )
        if preflight:
            return preflight

        if "registry" in intent and self.consensus is not None:
            if not self.consensus.is_leader:
                self.consensus.initiate_election()
            if not self.flux.commit_cluster_registry(intent):
                return ["consensus_rejected: leader authorization required for registry mutation"]
        if stage and self._agent:
            errors = self._agent.stage_intent(intent)
            if errors:
                return errors
        if not self.is_open or self._link is None:
            raise RuntimeError("Serial link is not open")
        fast_frame = FastPathSerializer.try_encode(intent)
        if fast_frame is not None:
            self.send_fastpath(fast_frame)
            return []
        payload = json.dumps(intent, separators=(",", ":")) + "\n"
        self._link.write(payload.encode("utf-8"))
        self._link.flush()
        return []

    def send_cluster_registry_mutation(
        self,
        units: dict[str, dict[str, Any]],
        *,
        use_mesh_2pc: bool = True,
    ) -> list[str]:
        """Run 2PC mesh sync then commit registry units across the cluster."""
        if not use_mesh_2pc:
            return self.send_intent({"registry": {"units": units}}, stage=False)

        mutation = {"units": units}
        transport = ControllerClusterTransport(self)
        if not self.mesh_synchronizer.execute_cluster_mutation(mutation, transport):
            return ["mesh_2pc_aborted: pre-flight rejected by one or more nodes"]
        return []

    def compile_vibe_for_wire(
        self, prompt: str, *, stage: bool = True
    ) -> tuple[bytes | None, dict[str, Any], list[str], str]:
        """Compile natural language to validated wire bytes (binwire or JSON line)."""
        from .vibe_pipeline import compile_vibe_wire_payload

        free_heap = self.available_heap_bytes() if self.is_open else 48_000
        result = compile_vibe_wire_payload(
            prompt,
            agent=self._agent if stage else None,
            resource_orchestrator=self.resource_orchestrator,
            free_heap=free_heap,
            stage=stage,
        )
        return result.payload, result.intent, result.errors, result.wire_format

    def send_fastpath(self, frame: bytes) -> None:
        """Send a pre-packed binwire (##) or RPP (#P) frame (no JSON on device)."""
        if self._enable_secure_wire:
            if BinwireEncoder.is_fastpath_frame(frame):
                frame = self.secure_wire.wrap_binwire_frame(frame)
            elif HostRPPCompiler.is_rpp_frame(frame):
                frame = self.secure_wire.wrap_rpp_frame(frame)
            elif not SecureWireEncoder.is_secure_frame(frame):
                raise ValueError("binary frame missing recognized magic header (##, #P, or #A)")
            if len(frame) != SECURE_WIRE_FRAME_LEN:
                raise ValueError(
                    f"secure wire frame must be {SECURE_WIRE_FRAME_LEN} bytes, got {len(frame)}"
                )
        elif len(frame) not in (BINWIRE_FRAME_LEN, RPP_FRAME_LEN):
            raise ValueError(
                f"binary frame must be {BINWIRE_FRAME_LEN} or {RPP_FRAME_LEN} bytes, got {len(frame)}"
            )
        elif not (BinwireEncoder.is_fastpath_frame(frame) or HostRPPCompiler.is_rpp_frame(frame)):
            raise ValueError("binary frame missing recognized magic header (## or #P)")
        if not self.is_open or self._link is None:
            raise RuntimeError("Serial link is not open")
        self._link.write(frame)
        self._link.flush()

    def send_rpp(self, frame: bytes) -> None:
        """Send a pre-packed RPP (#P) remote procedure frame."""
        if self._enable_secure_wire:
            frame = self.secure_wire.wrap_rpp_frame(frame)
            if len(frame) != SECURE_WIRE_FRAME_LEN:
                raise ValueError(
                    f"secure wire frame must be {SECURE_WIRE_FRAME_LEN} bytes, got {len(frame)}"
                )
        elif len(frame) != RPP_FRAME_LEN:
            raise ValueError(f"RPP frame must be {RPP_FRAME_LEN} bytes, got {len(frame)}")
        elif not HostRPPCompiler.is_rpp_frame(frame):
            raise ValueError("RPP frame missing magic header")
        if not self.is_open or self._link is None:
            raise RuntimeError("Serial link is not open")
        self._link.write(frame)
        self._link.flush()

    def send_delta_mutation(
        self,
        slot_updates: dict[int, int],
        *,
        transaction_sequence_id: int = 1,
    ) -> list[str]:
        """Send bitmapped structural delta frame (no JSON on wire)."""
        if not self.is_open or self._link is None:
            raise RuntimeError("Serial link is not open")
        frame = DeltaEncoder.pack_delta(
            slot_updates, transaction_sequence_id=transaction_sequence_id
        )
        self._link.write(frame)
        self._link.flush()
        return []

    def send_bitmap_delta(
        self,
        slot_id: int,
        operational_frequency: int,
        *,
        sequence_id: int = 1,
    ) -> list[str]:
        """Send fixed-width ##D bitmapped delta overlay (single frequency, zero JSON)."""
        if not self.is_open or self._link is None:
            raise RuntimeError("Serial link is not open")
        frame = BitmappedDeltaCompiler.compile_bitmap_delta(
            slot_id, operational_frequency, sequence_id
        )
        if len(frame) != BITMAP_DELTA_FRAME_LEN:
            return [f"bitmap_delta_rejected: expected {BITMAP_DELTA_FRAME_LEN} bytes"]
        logger.info(
            "[BITMAP DELTA] slot=%d freq=%d seq=%d (%d bytes)",
            slot_id,
            operational_frequency,
            sequence_id,
            len(frame),
        )
        self._link.write(frame)
        self._link.flush()
        return []

    def send_vector_fence_patch(
        self,
        interrupt_source_id: int,
        machine_code: bytes,
        *,
        transaction_id: int = 1,
    ) -> list[str]:
        """Stream `#I` IRAM ISR hot-patch with position-independent machine bytes."""
        if len(machine_code) > MAX_VECTOR_PATCH_BYTES:
            return [f"vector_patch_rejected: payload exceeds {MAX_VECTOR_PATCH_BYTES} bytes"]
        if not self.is_open or self._link is None:
            raise RuntimeError("Serial link is not open")
        try:
            frame = HostVectorCompiler.compile_vector_patch(
                interrupt_source_id,
                machine_code,
                transaction_id=transaction_id,
            )
        except ValueError as exc:
            return [f"vector_patch_rejected: {exc}"]
        logger.info(
            "[VECTOR FENCE] channel=%d bytes=%d tx=%d wire=%d",
            interrupt_source_id,
            len(machine_code),
            transaction_id,
            len(frame),
        )
        self._link.write(frame)
        self._link.flush()
        return []

    def send_stream_frame(
        self,
        unit_id: int,
        operational_mode: int,
        baseline_frequency: int,
    ) -> list[str]:
        """Send fixed-width `#S` cross-core stream intent frame (zero JSON)."""
        if not self.is_open or self._link is None:
            raise RuntimeError("Serial link is not open")
        frame = HostStreamPacker.pack_stream_frame(
            unit_id, operational_mode, baseline_frequency
        )
        if len(frame) != STREAM_FRAME_LEN:
            return [f"stream_frame_rejected: expected {STREAM_FRAME_LEN} bytes"]
        logger.info(
            "[STREAM] unit=%d mode=%d freq=%d (%d bytes)",
            unit_id,
            operational_mode,
            baseline_frequency,
            len(frame),
        )
        self._link.write(frame)
        self._link.flush()
        return []

    def send_branch_flatten(
        self,
        condition_id: int,
        target_function_slot: int,
        execution_tier: int = 3,
    ) -> list[str]:
        """Send fixed-width #F branch-flatten jump vector (zero JSON, direct dispatch)."""
        if not self.is_open or self._link is None:
            raise RuntimeError("Serial link is not open")
        frame = BranchFlattenCompiler.compile_jump_vector(
            condition_id, target_function_slot, execution_tier
        )
        if len(frame) != FLATTEN_FRAME_LEN:
            return [f"branch_flatten_rejected: expected {FLATTEN_FRAME_LEN} bytes"]
        logger.info(
            "[BRANCH FLATTEN] condition=%d slot=%d tier=%d (%d bytes)",
            condition_id,
            target_function_slot,
            execution_tier,
            len(frame),
        )
        self._link.write(frame)
        self._link.flush()
        return []

    def unified_orchestrator(self) -> UnifiedOrchestrationController:
        """Return master state-sync orchestrator bound to the active serial transport."""
        if not self.is_open or self._link is None:
            raise RuntimeError("Serial link is not open")
        return UnifiedOrchestrationController(
            self._link,
            require_registry_signature=self._require_registry_signature,
        )

    def send_graph_registry_delta(
        self,
        units: dict[str, dict[str, Any]],
        changed_node: str,
        *,
        transaction_sequence_id: int = 1,
    ) -> list[str]:
        """Compute DAG cascade and transmit compact bitmask delta."""
        graph = StateGraphEngine.from_units(units)
        graph_errors = graph.validate_dag()
        if graph_errors:
            return graph_errors
        frame = DeltaEncoder.encode_graph_mutation(
            units,
            changed_node,
            transaction_sequence_id=transaction_sequence_id,
        )
        if frame is None:
            return ["delta_encode_failed: no slot updates for cascade"]
        if not self.is_open or self._link is None:
            raise RuntimeError("Serial link is not open")
        logger.info(
            "[GRAPH DELTA] Cascade %s -> %s bytes on wire",
            graph.compute_mutation_delta_paths(changed_node),
            len(frame),
        )
        self._link.write(frame)
        self._link.flush()
        return []

    def send_memory_overlay(
        self,
        target_address: int,
        machine_instructions: bytes,
    ) -> list[str]:
        """Compile and transmit IRAM memory overlay frame (#M magic)."""
        if not HardwareMemoryCompiler.verify_address_safety(target_address):
            return [
                f"overlay_rejected: address 0x{target_address:08X} outside IRAM fence "
                f"0x{IRAM_EXEC_START:08X}-0x{IRAM_EXEC_END:08X}"
            ]
        if len(machine_instructions) > MAX_OVERLAY_PAYLOAD:
            return [f"overlay_rejected: payload exceeds {MAX_OVERLAY_PAYLOAD} bytes"]
        try:
            frame = HardwareMemoryCompiler.compile_memory_overlay(
                target_address, machine_instructions
            )
        except ValueError as exc:
            return [str(exc)]
        frame_errors = HardwareMemoryCompiler.validate_overlay_frame(frame)
        if frame_errors:
            return frame_errors
        if not self.is_open or self._link is None:
            raise RuntimeError("Serial link is not open")
        logger.info(
            "[OVERLAY] IRAM patch 0x%08X (%s payload bytes, %s wire bytes)",
            target_address,
            len(machine_instructions),
            len(frame),
        )
        self._link.write(frame)
        self._link.flush()
        return []

    def send_relay_intent(
        self,
        intent: dict[str, Any],
        *,
        stage: bool = True,
        sign: bool | None = None,
    ) -> list[str]:
        """Validate intent fits cross-core ring frames, then transmit JSON line."""
        should_sign = self._sign_intents if sign is None else sign
        payload_intent = sign_intent(intent) if should_sign else intent
        line = json.dumps(payload_intent, separators=(",", ":"))
        wrapped = StreamRelayEncoder.wrap_json_line(line)
        align_errors = StreamRelayEncoder.validate_frame_alignment(
            StreamRelayEncoder.chunk_payload(wrapped)
        )
        if align_errors:
            return align_errors
        return self.send_intent(intent, stage=stage, sign=sign)

    def compile_and_send_jit(
        self,
        c_code: str,
        *,
        unit_id: str = "custom_asm_routine",
        execute: bool = True,
        stage: bool = True,
        sign: bool | None = None,
    ) -> list[str]:
        """Compile C logic to Xtensa bytes and inject via native_jit intent."""
        from .jit_pipeline import M5JitPipeline

        result = M5JitPipeline().compile_vibe_to_jit_intent(
            c_code, unit_id=unit_id, execute=execute
        )
        if not result.ok:
            return result.errors
        return self.send_intent(result.intent, stage=stage, sign=sign)

    def compile_and_send_jit_with_delta(
        self,
        c_code: str,
        units: dict[str, dict[str, Any]],
        changed_node: str,
        *,
        unit_id: str = "custom_asm_routine",
        execute: bool = True,
        transaction_sequence_id: int = 1,
    ) -> list[str]:
        """Hot-load JIT patch then stream differential registry delta frame."""
        from .jit_pipeline import M5JitPipeline

        pipeline = M5JitPipeline()
        result = pipeline.compile_jit_with_registry_delta(
            c_code,
            units,
            changed_node,
            unit_id=unit_id,
            execute=execute,
            transaction_sequence_id=transaction_sequence_id,
        )
        if not result.ok:
            return result.errors
        errors = self.send_intent(result.intent, stage=False)
        if errors:
            return errors
        if result.delta_frame is not None:
            if not self.is_open or self._link is None:
                raise RuntimeError("Serial link is not open")
            self._link.write(result.delta_frame)
            self._link.flush()
        return []

    def send_vector_clock_sync(self, sync_vector: dict[str, int]) -> list[str]:
        """Push host logical clock heights to firmware causal telemetry builder."""
        if self.flux.vector_clock is not None:
            self.flux.vector_clock.apply_sync_vector(sync_vector)
        return self.send_intent({"vector_clock_sync": sync_vector}, stage=False)

    def read_frame(self) -> TelemetryFrame | TimeTravelFrame | None:
        if not self.is_open or self._link is None:
            raise RuntimeError("Serial link is not open")

        line = self._link.readline().decode("utf-8", errors="replace").strip()
        if not line:
            return None

        if line.startswith(TIME_TRAVEL_PREFIX) or (
            line.startswith("{") and "time_travel_journal_dump" in line
        ):
            return self._handle_time_travel_line(line)

        if line.startswith(VIRTUAL_EVENT_STREAM_PREFIX):
            payload = VirtualEventRouter.parse_event_line(line)
            if payload is not None:
                self.event_router.ingest_packet(payload)
                frame = TelemetryFrame(payload=payload, raw=line)
                return frame

        if line.startswith(HEALTH_VITALS_STREAM_PREFIX):
            vitals = AutonomousRemediationEngine.parse_vitals_line(line)
            if vitals is not None:
                unit_id, free_heap, jitter = vitals
                payload = {
                    "type": "health_vitals",
                    "unit_id": unit_id,
                    "metrics": {"free_heap": free_heap, "task_jitter_ms": jitter},
                }
                frame = TelemetryFrame(payload=payload, raw=line)
                self._process_health_vitals(frame, unit_id, free_heap, jitter)
                return frame
            return None

        if line.startswith(TELEMETRY_STREAM_PREFIX):
            payload = AutonomousMitigationEngine.parse_telemetry_line(line)
            if payload is None:
                return None
            if payload.get("type") is None:
                payload["type"] = "telemetry"
            frame = TelemetryFrame(payload=payload, raw=line)
            self._process_frame(frame)
            return frame

        if not line.startswith("{"):
            return None

        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            return None

        if payload.get("type") == "telemetry":
            payload, repaired = self.flux.repair_telemetry(payload)
            if repaired:
                logger.info("[ECC] Repaired single-bit telemetry corruption in inbound frame")

        if payload.get("type") == "time_travel_journal_dump":
            return self._handle_time_travel_line(line)

        if payload.get("event_type") or payload.get("type") == "hardware_event":
            self.event_router.ingest_packet(payload)

        if payload.get("type") == "security_alarm":
            reason = payload.get("payload", {}).get("reason", "security_alarm")
            logger.warning("[SECURITY ALARM] %s", reason)

        frame = TelemetryFrame(payload=payload, raw=line)
        self._process_frame(frame)
        return frame

    def _handle_time_travel_line(self, line: str) -> TimeTravelFrame | None:
        if not self._replay_engine:
            return None
        replay = self._replay_engine.replay_from_serial_line(line)
        if replay is None:
            return None
        self.last_replay = replay
        if not replay.ok and self._on_replay_fault:
            self._on_replay_fault(replay)
        try:
            payload = json.loads(
                line[len(TIME_TRAVEL_PREFIX) :].strip()
                if line.startswith(TIME_TRAVEL_PREFIX)
                else line
            )
        except json.JSONDecodeError:
            payload = {"type": "time_travel_journal_dump", "raw": line}
        return TimeTravelFrame(payload=payload, raw=line, replay=replay)

    def _inject_remediation_token(self, token: bytes) -> None:
        if not token or not self.is_open or self._link is None:
            return
        self._link.write(token)
        self._link.flush()
        logger.info("[AUTOFENCE] Closed-loop remediation token injected (%s bytes)", len(token))

    def _process_health_vitals(
        self,
        frame: TelemetryFrame,
        unit_id: int,
        free_heap: int,
        jitter: int,
    ) -> None:
        if self._enable_dashboard:
            metrics = frame.payload.get("metrics", {})
            i2c_locked = bool(metrics.get("i2c_locked", False))
            snapshot = TerminalStateVisualizer.snapshot_from_vitals(
                unit_id,
                free_heap,
                jitter,
                typestate=self._dashboard_typestate,
                i2c_locked=i2c_locked,
            )
            TerminalStateVisualizer.render_system_matrix(snapshot)

        if self.remediation_engine is None:
            return
        token, repaired = self.remediation_engine.inspect_and_heal_profile(
            unit_id, free_heap, jitter
        )
        if repaired:
            self._inject_remediation_token(token)

    def _process_frame(self, frame: TelemetryFrame) -> None:
        if frame.payload.get("type") != "telemetry":
            return
        self.device_state.update(frame.payload)
        self.memory_profiler.update_device_snapshot(frame.payload)
        self.resource_orchestrator.evaluate_telemetry(frame.payload)
        remediated = False
        if self.remediation_engine is not None:
            token, remediated = self.remediation_engine.inspect_from_telemetry(frame.payload)
            if remediated:
                self._inject_remediation_token(token)
        if self.mitigation_engine is not None and not remediated:
            token = self.mitigation_engine.inspect_telemetry_and_heal(frame.payload)
            if token:
                self.send_fastpath(token)
                logger.info(
                    "[MITIGATION] Telemetry-driven binwire remediation injected (%s bytes)",
                    len(token),
                )
        patch = self.flux.resolve_intent_patch(frame.payload)
        if patch:
            self.send_intent(patch, stage=True)
        if self._agent:
            corrective = self._agent.observe_and_correct(frame.payload)
            if corrective:
                self.send_intent(corrective, stage=False)

    def run_agent_loop(
        self,
        *,
        tick_s: float = 0.01,
        should_stop: Callable[[], bool] | None = None,
    ) -> None:
        stop = should_stop or (lambda: False)
        while not stop():
            if self.consensus is not None:
                self.consensus.tick()
            self.read_frame()
            time.sleep(tick_s)


class UnifiedOrchestrationController:
    """
    Unified state synchronization core (Feature 61).

    Master host runtime: validates vibe/registry blocks, runs scheduler priority
    compilation, and emits minimal ##D bitmapped delta overlays on Fluxwire.
    """

    def __init__(
        self,
        transport_mesh: Any,
        *,
        require_registry_signature: bool = False,
        default_sequence_id: int = 101,
    ) -> None:
        self.transport = transport_mesh
        self.validator = IntentValidator(require_registry_signature=require_registry_signature)
        self.default_sequence_id = default_sequence_id

    def _transport_write(self, data: bytes) -> None:
        self.transport.write(data)
        flush = getattr(self.transport, "flush", None)
        if callable(flush):
            flush()

    @staticmethod
    def _extract_units_block(intent_block: dict[str, Any]) -> dict[str, Any]:
        units = intent_block.get("units")
        if isinstance(units, dict):
            return units
        registry = intent_block.get("registry")
        if isinstance(registry, dict):
            registry_units = registry.get("units")
            if isinstance(registry_units, dict):
                return registry_units
        return {}

    def synchronize_intent_delta(
        self,
        raw_intent_block: dict[str, Any],
        unit_slot: int,
        *,
        sequence_id: int | None = None,
    ) -> bool:
        logger.info("[ORCHESTRATOR] Initiating pre-flight schema contract audit...")

        if not self.validator.validate(raw_intent_block):
            logger.error("[VALIDATION FAILURE] Intent payload violates system invariants.")
            return False

        optimized_intent = HostSchedulerCompiler.compute_priority_matrix(raw_intent_block)
        units = self._extract_units_block(optimized_intent)
        if not units:
            logger.error("[ORCHESTRATOR] No units block found for delta synchronization.")
            return False

        seq = self.default_sequence_id if sequence_id is None else sequence_id

        for name, config in units.items():
            if not isinstance(config, dict):
                continue
            frequency = int(config.get("frequency_hz", 0) or 0)

            logger.info(
                "[COMPILER] Packaging dynamic delta updates for unit '%s' into slot %d...",
                name,
                unit_slot,
            )
            binary_payload = BitmappedDeltaCompiler.compile_bitmap_delta(
                slot_id=unit_slot,
                operational_frequency=frequency,
                sequence_id=seq,
            )
            self._transport_write(binary_payload)
            logger.info("[SUCCESS] Bitmapped system delta flushed over the network wire.")
            return True

        return False

    def synchronize_branch_flatten(
        self,
        condition_id: int,
        target_function_slot: int,
        *,
        execution_tier: int = 3,
    ) -> bool:
        """Compile and flush a flattened branch jump vector over the transport mesh."""
        frame = BranchFlattenCompiler.compile_jump_vector(
            condition_id, target_function_slot, execution_tier
        )
        self._transport_write(frame)
        logger.info(
            "[ORCHESTRATOR] Branch flatten vector condition=%d slot=%d tier=%d emitted",
            condition_id,
            target_function_slot,
            execution_tier,
        )
        return True

    def synchronize_vector_fence(
        self,
        interrupt_source_id: int,
        machine_code: bytes,
        *,
        transaction_id: int = 1,
    ) -> bool:
        """Compile and flush an IRAM ISR vector patch over the transport mesh."""
        try:
            frame = HostVectorCompiler.compile_vector_patch(
                interrupt_source_id,
                machine_code,
                transaction_id=transaction_id,
            )
        except ValueError:
            return False
        self._transport_write(frame)
        logger.info(
            "[ORCHESTRATOR] Vector fence channel=%d bytes=%d tx=%d emitted",
            interrupt_source_id,
            len(machine_code),
            transaction_id,
        )
        return True

    def synchronize_stream_frame(
        self,
        unit_id: int,
        operational_mode: int,
        baseline_frequency: int,
    ) -> bool:
        """Compile and flush a cross-core stream intent frame over the transport mesh."""
        frame = HostStreamPacker.pack_stream_frame(
            unit_id, operational_mode, baseline_frequency
        )
        self._transport_write(frame)
        logger.info(
            "[ORCHESTRATOR] Stream frame unit=%d mode=%d freq=%d emitted",
            unit_id,
            operational_mode,
            baseline_frequency,
        )
        return True
