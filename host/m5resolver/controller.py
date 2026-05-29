from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

import serial

from .agent import AgenticController, DeviceState
from .fluxwire import FluxGraph


@dataclass
class TelemetryFrame:
    payload: dict[str, Any]
    raw: str


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
    ) -> None:
        self.port = port
        self.baud = baud
        self.timeout = timeout
        self._link: serial.Serial | None = None
        self.device_state = DeviceState()
        self.flux = FluxGraph()
        self._agent: AgenticController | None = None
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

    def read_frame(self) -> TelemetryFrame | None:
        if not self.is_open or self._link is None:
            raise RuntimeError("Serial link is not open")

        line = self._link.readline().decode("utf-8", errors="replace").strip()
        if not line or not line.startswith("{"):
            return None

        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            return None

        frame = TelemetryFrame(payload=payload, raw=line)
        self._process_frame(frame)
        return frame

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
            frame = self.read_frame()
            if frame is None:
                time.sleep(tick_s)
