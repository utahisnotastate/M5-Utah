from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any, Literal

from .agent import AgenticController
from .fastpath import FastPathSerializer
from .optimizer import DEFAULT_AVAILABLE_HEAP
from .registry_ops import RegistryStore
from .resource_orchestrator import HostResourceOrchestrator
from .safety import validate_intent_safety
from .validation import validate_intent_payload
from .vibe_compiler import compile_vibe_to_intent

logger = logging.getLogger("m5resolver.vibe_pipeline")

WireFormat = Literal["fastpath", "json", "error"]


@dataclass
class VibeWireResult:
    payload: bytes | None
    intent: dict[str, Any]
    errors: list[str]
    wire_format: WireFormat

    @property
    def ok(self) -> bool:
        return self.payload is not None and not self.errors


def compile_vibe_wire_payload(
    prompt: str,
    *,
    agent: AgenticController | None = None,
    resource_orchestrator: HostResourceOrchestrator | None = None,
    registry_store: RegistryStore | None = None,
    free_heap: int = DEFAULT_AVAILABLE_HEAP,
    stage: bool = True,
) -> VibeWireResult:
    """
    Map natural language to schema-safe intent, validate safety/resources,
    and emit either a fixed-width binwire frame or JSON line bytes.
    """
    intent = compile_vibe_to_intent(prompt)
    errors: list[str] = list(validate_intent_payload(intent))
    errors.extend(validate_intent_safety(intent))

    orchestrator = resource_orchestrator or HostResourceOrchestrator()
    errors.extend(orchestrator.preflight_transmit(intent, free_heap=free_heap))

    if stage and agent is not None:
        errors.extend(agent.stage_intent(intent))

    if errors:
        return VibeWireResult(payload=None, intent=intent, errors=errors, wire_format="error")

    if registry_store is not None and "registry" in intent:
        reg_errors = registry_store.merge_runtime_units(intent["registry"].get("units", {}))
        if reg_errors:
            return VibeWireResult(
                payload=None, intent=intent, errors=reg_errors, wire_format="error"
            )

    frame = FastPathSerializer.try_encode(intent)
    if frame is not None:
        logger.info("[VIBE] Fast-path binwire frame (%s bytes) for prompt", len(frame))
        return VibeWireResult(payload=frame, intent=intent, errors=[], wire_format="fastpath")

    wire = json.dumps(intent, separators=(",", ":")).encode("utf-8") + b"\n"
    return VibeWireResult(payload=wire, intent=intent, errors=[], wire_format="json")
