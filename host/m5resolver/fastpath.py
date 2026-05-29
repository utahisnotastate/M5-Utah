from __future__ import annotations

import json
import logging
from typing import Any

from .binwire import BINWIRE_FRAME_LEN, BinwireEncoder
from .rpp_compiler import RPP_FRAME_LEN, HostRPPCompiler

logger = logging.getLogger("m5resolver.fastpath")


class FastPathSerializer:
    """
    Zero-allocation fast-path binary serialization for vibe-coded GPIO intents.

    Wraps BinwireEncoder (`##` magic, !BBHI layout) used by firmware BinwireDecoder.
    """

    @staticmethod
    def pack_intent_vector(unit_id: int, pin: int, frequency: int, state: int) -> bytes:
        return BinwireEncoder.pack_unit_mutation(unit_id, pin, frequency, state)

    @staticmethod
    def try_encode(intent_data: dict[str, Any]) -> bytes | None:
        """Return a fixed-width binwire or RPP frame when intent qualifies for fast-path."""
        rpp_frame = HostRPPCompiler.encode_intent(intent_data)
        if rpp_frame is not None:
            structural_keys = set(intent_data.keys()) - {"rpp", "security", "fastpath", "intent"}
            if not structural_keys:
                logger.info("[RPP] Encoded remote procedure frame (%s bytes)", len(rpp_frame))
                return rpp_frame

        intent_block = intent_data.get("intent")
        if isinstance(intent_block, dict) and intent_block.get("action") == "rpp_execute":
            params = intent_block.get("parameters", {})
            if isinstance(params, dict):
                return HostRPPCompiler.compile_rpp_frame(
                    unit_id=int(params.get("unit_id", 0)),
                    functional_opcode=int(
                        params.get("opcode", params.get("functional_opcode", 0))
                    ),
                    data_vector=int(params.get("data_vector", params.get("parameter", 0))),
                    sequence_id=int(params.get("sequence_id", 0)),
                )

        if isinstance(intent_block, dict) and intent_block.get("action") == "fast_track_gpio":
            params = intent_block.get("parameters", {})
            if isinstance(params, dict):
                frame = FastPathSerializer.pack_intent_vector(
                    unit_id=int(params.get("unit_id", 0)),
                    pin=int(params.get("pin", 0)),
                    frequency=int(params.get("frequency_hz", params.get("frequency", 0))),
                    state=int(params.get("state_mask", params.get("state_flag", 0))),
                )
                logger.info(
                    "[FASTPATH] Encoded fast_track_gpio unit=%s pin=%s (%s bytes)",
                    params.get("unit_id", 0),
                    params.get("pin", 0),
                    len(frame),
                )
                return frame

        if "binwire" in intent_data:
            structural_keys = set(intent_data.keys()) - {"binwire", "security", "fastpath", "intent"}
            if not structural_keys:
                frame = BinwireEncoder.encode_intent({"binwire": intent_data["binwire"]})
                if frame is not None:
                    return frame

        if intent_data.get("fastpath") is True:
            frame = BinwireEncoder.encode_intent(intent_data)
            if frame is not None:
                return frame

        return None

    @staticmethod
    def process_and_route(intent_data: dict[str, Any]) -> bytes:
        """
        Return raw binwire bytes for fast-path intents, otherwise UTF-8 JSON payload.
        """
        frame = FastPathSerializer.try_encode(intent_data)
        if frame is not None:
            return frame
        return json.dumps(intent_data, separators=(",", ":")).encode("utf-8")

    @staticmethod
    def is_fastpath_payload(payload: bytes) -> bool:
        if len(payload) == BINWIRE_FRAME_LEN and BinwireEncoder.is_fastpath_frame(payload):
            return True
        return len(payload) == RPP_FRAME_LEN and HostRPPCompiler.is_rpp_frame(payload)
