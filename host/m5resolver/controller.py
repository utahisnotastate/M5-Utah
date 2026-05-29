from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

import serial

from .agent import AgenticController, DeviceState
from .fluxwire import FluxGraph
from .replay_engine import HostReplayEngine, ReplayResult, TIME_TRAVEL_PREFIX


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
        on_replay_fault: Callable[[ReplayResult], None] | None = None,
    ) -> None:
        self.port = port
        self.baud = baud
        self.timeout = timeout
        self._link: serial.Serial | None = None
        self.device_state = DeviceState()
        self.flux = FluxGraph()
        self._agent: AgenticController | None = None
        self._replay_engine: HostReplayEngine | None = None
        self._on_replay_fault = on_replay_fault
        self.last_replay: ReplayResult | None = None
        if enable_time_travel:
            schema = telemetry_schema_path or "schemas/telemetry.schema.json"
            self._replay_engine = HostReplayEngine(telemetry_schema_path=schema)
        if enable_agent and registry_path:
            self._agent = AgenticController(
                registry_path=registry_path,
                telemetry_schema_path=telemetry_schema_path,
                on_corrective_intent=self._on_corrective_intent,
            )

    def _on_corrective_intent(self, intent: dict[str, Any]) -> None:
        if self.is_open:
            self.send_intent(intent)

    def open(self) -> None:
        self._link = serial.Serial(self.port, self.baud, timeout=self.timeout)
        time.sleep(1.25)

    def close(self) -> None:
        if self._link and self._link.is_open:
            self._link.close()
        self._link = None

    @property
    def is_open(self) -> bool:
        return self._link is not None and self._link.is_open

    def send_intent(self, intent: dict[str, Any], *, stage: bool = True) -> list[str]:
        if stage and self._agent:
            errors = self._agent.stage_intent(intent)
            if errors:
                return errors
        if not self.is_open or self._link is None:
            raise RuntimeError("Serial link is not open")
        payload = json.dumps(intent, separators=(",", ":")) + "\n"
        self._link.write(payload.encode("utf-8"))
        self._link.flush()
        return []

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

        if not line.startswith("{"):
            return None

        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            return None

        if payload.get("type") == "time_travel_journal_dump":
            return self._handle_time_travel_line(line)

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

    def _process_frame(self, frame: TelemetryFrame) -> None:
        if frame.payload.get("type") != "telemetry":
            return
        self.device_state.update(frame.payload)
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
            self.read_frame()
            time.sleep(tick_s)
