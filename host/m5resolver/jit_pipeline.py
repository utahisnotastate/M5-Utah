"""
m5-jit pipeline — position-independent hot-load + differential registry patching.

Aligns ADR 0001 (intent-first), ADR 0002 (thin firmware), ADR 0003 (registry units),
ADR 0011 (runtime JIT), and ADR 0014 (delta compression).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .delta_engine import DeltaEncoder
from .graph_engine import StateGraphEngine
from .jit_compiler import (
    MAX_JIT_CODE_BYTES,
    HostJitCompiler,
    validate_native_jit_block,
    verify_iram_payload_safe,
)
from .validation import validate_intent_payload


@dataclass
class JitPipelineResult:
    intent: dict[str, Any] | None
    delta_frame: bytes | None
    errors: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return self.intent is not None and not self.errors


class M5JitPipeline:
    """
    Deterministic native assembly hot-loading with optional differential registry patch.

    Host cross-compiles vibe logic → native_jit intent; optionally emits 0xDE delta
    frames for registry slot updates without full JSON redeploy.
    """

    def __init__(self, compiler: HostJitCompiler | None = None) -> None:
        self.compiler = compiler or HostJitCompiler()

    def compile_vibe_to_jit_intent(
        self,
        c_code: str,
        *,
        unit_id: str = "custom_asm_routine",
        execute: bool = True,
    ) -> JitPipelineResult:
        raw = self.compiler.compile_intent_to_assembly(c_code)
        if raw is None:
            return JitPipelineResult(
                intent=None,
                delta_frame=None,
                errors=["jit_compile_failed: toolchain unavailable or compilation error"],
            )
        if not verify_iram_payload_safe(len(raw)):
            return JitPipelineResult(
                intent=None,
                delta_frame=None,
                errors=[f"jit_payload_unsafe: {len(raw)} bytes exceeds IRAM envelope"],
            )
        intent = HostJitCompiler.pack_jit_intent(raw, unit_id=unit_id, execute=execute)
        schema_errors = validate_intent_payload(intent) + validate_native_jit_block(
            intent["native_jit"]
        )
        if schema_errors:
            return JitPipelineResult(intent=None, delta_frame=None, errors=schema_errors)
        return JitPipelineResult(intent=intent, delta_frame=None, errors=[])

    def compute_registry_delta(
        self,
        units: dict[str, dict[str, Any]],
        changed_node: str,
        *,
        transaction_sequence_id: int = 1,
    ) -> bytes | None:
        graph = StateGraphEngine.from_units(units)
        if graph.validate_dag():
            return None
        return DeltaEncoder.encode_graph_mutation(
            units,
            changed_node,
            transaction_sequence_id=transaction_sequence_id,
        )

    def compile_jit_with_registry_delta(
        self,
        c_code: str,
        units: dict[str, dict[str, Any]],
        changed_node: str,
        *,
        unit_id: str = "custom_asm_routine",
        execute: bool = True,
        transaction_sequence_id: int = 1,
    ) -> JitPipelineResult:
        jit_result = self.compile_vibe_to_jit_intent(c_code, unit_id=unit_id, execute=execute)
        if not jit_result.ok:
            return jit_result
        delta = self.compute_registry_delta(
            units, changed_node, transaction_sequence_id=transaction_sequence_id
        )
        return JitPipelineResult(intent=jit_result.intent, delta_frame=delta, errors=[])


M5_JIT_CAPABILITY = "runtime_jit_linker"
M5_JIT_IRAM_LIMIT_BYTES = MAX_JIT_CODE_BYTES
