from __future__ import annotations

import json
import time
from dataclasses import dataclass
from typing import Any

import serial


@dataclass
class TelemetryFrame:
    payload: dict[str, Any]
    raw: str


class IntentController:
    """Bidirectional serial bridge for JSON intents and telemetry."""

    def __init__(self, port: str, baud: int = 115200, timeout: float = 0.2) -> None:
        self.port = port
        self.baud = baud
        self.timeout = timeout
        self._link: serial.Serial | None = None

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

    def send_intent(self, intent: dict[str, Any]) -> None:
        if not self.is_open or self._link is None:
            raise RuntimeError("Serial link is not open")
        payload = json.dumps(intent, separators=(",", ":")) + "\n"
        self._link.write(payload.encode("utf-8"))
        self._link.flush()

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

        return TelemetryFrame(payload=payload, raw=line)
