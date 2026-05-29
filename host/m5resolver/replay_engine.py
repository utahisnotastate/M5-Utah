from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger("m5resolver.time_travel")

TIME_TRAVEL_PREFIX = "[FLUXWIRE_TIME_TRAVEL_STREAM]:"
HEAP_FAULT_THRESHOLD = 30000


@dataclass
class ReplayResult:
    ok: bool
    records_analyzed: int = 0
    fault_fingerprint: str | None = None
    fault_heap: int | None = None
    timeline: list[dict[str, Any]] = field(default_factory=list)


class HostReplayEngine:
    """
    Offline deterministic replay of device time-travel journal dumps.
    Reconstructs crash timelines from firmware state snapshots.
    """

    def __init__(
        self,
        telemetry_schema_path: str | Path = "schemas/telemetry.schema.json",
        intent_schema_path: str | Path = "schemas/intent.schema.json",
    ) -> None:
        self.telemetry_schema_path = Path(telemetry_schema_path)
        self.intent_schema_path = Path(intent_schema_path)
        if self.telemetry_schema_path.exists():
            self.telemetry_schema = json.loads(self.telemetry_schema_path.read_text(encoding="utf-8"))
        else:
            self.telemetry_schema = {}
        if self.intent_schema_path.exists():
            self.intent_schema = json.loads(self.intent_schema_path.read_text(encoding="utf-8"))
        else:
            self.intent_schema = {}

    @staticmethod
    def extract_journal_json(raw_line: str) -> str | None:
        if raw_line.startswith(TIME_TRAVEL_PREFIX):
            return raw_line[len(TIME_TRAVEL_PREFIX) :].strip()
        return None

    def reconstruct_hardware_crash_timeline(self, journal_payload_raw: str) -> ReplayResult:
        try:
            payload = json.loads(journal_payload_raw)
        except json.JSONDecodeError:
            logger.error("Failed to decode time-travel stream frame")
            return ReplayResult(ok=False)

        if payload.get("type") != "time_travel_journal_dump":
            return ReplayResult(ok=False)

        records: list[dict[str, Any]] = list(payload.get("journal_records", []))
        logger.info("[TIME TRAVEL] Unpacking %s state snapshots", len(records))

        timeline: list[dict[str, Any]] = []
        for idx, state in enumerate(records):
            heap = int(state.get("allocated_heap_remaining", 100000))
            fingerprint = str(state.get("intent_fingerprint", "unknown"))
            entry = {
                "index": idx,
                "relative_ms": state.get("relative_ms"),
                "heap": heap,
                "fingerprint": fingerprint,
            }
            timeline.append(entry)
            logger.info(" -> Snapshot [-%s]: heap=%s action=%s", idx, heap, fingerprint)

            if heap < HEAP_FAULT_THRESHOLD:
                logger.error(
                    "[FAULT] Intent '%s' associated with heap exhaustion (%s bytes)",
                    fingerprint,
                    heap,
                )
                return ReplayResult(
                    ok=False,
                    records_analyzed=len(records),
                    fault_fingerprint=fingerprint,
                    fault_heap=heap,
                    timeline=timeline,
                )

        return ReplayResult(ok=True, records_analyzed=len(records), timeline=timeline)

    def replay_from_serial_line(self, line: str) -> ReplayResult | None:
        extracted = self.extract_journal_json(line)
        if extracted:
            return self.reconstruct_hardware_crash_timeline(extracted)
        if line.startswith("{") and "time_travel_journal_dump" in line:
            return self.reconstruct_hardware_crash_timeline(line)
        return None
