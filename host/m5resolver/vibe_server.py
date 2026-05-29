from __future__ import annotations

import argparse
import json
import logging
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from .agent import AgenticController
from .controller import IntentController
from .registry_ops import RegistryStore
from .resource_orchestrator import HostResourceOrchestrator
from .vibe_pipeline import compile_vibe_wire_payload

logger = logging.getLogger("m5resolver.vibe_server")

STATIC_DIR = Path(__file__).parent / "static"


class VibeGatewayHandler(BaseHTTPRequestHandler):
    """WebUSB/WebSerial IDE broker — compiles vibe prompts to validated wire payloads."""

    registry_store: RegistryStore
    agent: AgenticController
    orchestrator: HostResourceOrchestrator
    serial_controller: IntentController | None

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A003
        logger.debug(format, *args)

    def _send_json(self, status: int, payload: dict[str, Any]) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _send_bytes(self, status: int, payload: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(payload)

    def do_OPTIONS(self) -> None:  # noqa: N802
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self) -> None:  # noqa: N802
        if self.path in ("/", "/index.html", "/ide"):
            html = (STATIC_DIR / "vibe-ide.html").read_text(encoding="utf-8")
            self._send_bytes(200, html.encode("utf-8"), "text/html; charset=utf-8")
            return
        if self.path == "/health":
            self._send_json(
                200,
                {
                    "ok": True,
                    "service": "vibe-gateway",
                    "serial_attached": self.serial_controller is not None
                    and self.serial_controller.is_open,
                },
            )
            return
        if self.path == "/registry":
            self._send_json(200, self.registry_store.load_raw())
            return
        self._send_json(404, {"error": "not_found"})

    def _read_json_body(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0:
            return {}
        return json.loads(self.rfile.read(length).decode("utf-8"))

    def _compile(self, prompt: str, *, stage: bool = True):
        free_heap = (
            self.serial_controller.available_heap_bytes()
            if self.serial_controller is not None and self.serial_controller.is_open
            else 48_000
        )
        return compile_vibe_wire_payload(
            prompt,
            agent=self.agent if stage else None,
            resource_orchestrator=self.orchestrator,
            registry_store=self.registry_store,
            free_heap=free_heap,
            stage=stage,
        )

    def do_POST(self) -> None:  # noqa: N802
        if self.path == "/compile_vibe":
            data = self._read_json_body()
            prompt = data.get("prompt", "")
            result = self._compile(prompt, stage=not bool(data.get("dry_run", False)))
            if not result.ok:
                self._send_json(400, {"errors": result.errors, "intent": result.intent})
                return

            if data.get("server_inject") and self.serial_controller is not None:
                inject_errors = self._inject_via_controller(result.payload, result.wire_format)
                if inject_errors:
                    self._send_json(500, {"errors": inject_errors})
                    return

            self.send_response(200)
            self.send_header("Content-Type", "application/octet-stream")
            self.send_header("X-Wire-Format", result.wire_format)
            self.send_header("X-Intent-Json", json.dumps(result.intent, separators=(",", ":")))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Expose-Headers", "X-Wire-Format, X-Intent-Json")
            self.send_header("Content-Length", str(len(result.payload)))
            self.end_headers()
            self.wfile.write(result.payload)
            return

        if self.path == "/generate_intent":
            data = self._read_json_body()
            prompt = data.get("prompt", "")
            dry_run = bool(data.get("dry_run", False))
            result = self._compile(prompt, stage=not dry_run)
            if not result.ok:
                self._send_json(400, {"errors": result.errors})
                return
            self._send_json(
                200,
                {
                    "intent": result.intent,
                    "dry_run": dry_run,
                    "wire_format": result.wire_format,
                    "fastpath": result.wire_format == "fastpath",
                    "frame_hex": result.payload.hex() if result.wire_format == "fastpath" else None,
                },
            )
            return

        self._send_json(404, {"error": "not_found"})

    def _inject_via_controller(self, payload: bytes, wire_format: str) -> list[str]:
        controller = self.serial_controller
        if controller is None or not controller.is_open:
            return ["serial_not_connected"]
        try:
            if wire_format == "fastpath":
                controller.send_fastpath(payload)
            else:
                controller._link.write(payload)  # noqa: SLF001 — newline JSON already encoded
                controller._link.flush()
        except Exception as exc:  # noqa: BLE001 — surface to HTTP client
            return [f"serial_inject_failed: {exc}"]
        return []


def start_vibe_ide(
    host: str = "127.0.0.1",
    port: int = 8023,
    registry_path: str = "registry/units.json",
    telemetry_schema_path: str = "schemas/telemetry.schema.json",
    *,
    serial_port: str | None = None,
    baudrate: int = 115200,
) -> None:
    """Start the zero-install WebUSB/WebSerial vibe gateway."""
    registry_store = RegistryStore(registry_path)
    agent = AgenticController(registry_path, telemetry_schema_path)
    orchestrator = HostResourceOrchestrator()

    serial_controller: IntentController | None = None
    if serial_port:
        serial_controller = IntentController(
            serial_port,
            baudrate,
            registry_path=registry_path,
            telemetry_schema_path=telemetry_schema_path,
            enable_agent=False,
        )
        serial_controller.open()
        logger.info("[INIT] Host serial bridge attached on %s @ %s", serial_port, baudrate)

    handler = VibeGatewayHandler
    handler.registry_store = registry_store
    handler.agent = agent
    handler.orchestrator = orchestrator
    handler.serial_controller = serial_controller

    server = ThreadingHTTPServer((host, port), handler)
    logger.info("[INIT] m5-utah WebUSB vibe gateway at http://%s:%s", host, port)
    print(f"[*] m5-utah Vibe Gateway running at http://{host}:{port}")
    print("[*] Open in Chrome/Edge — connect device via WebSerial or pass --serial for host bridge")
    try:
        server.serve_forever()
    finally:
        if serial_controller is not None and serial_controller.is_open:
            serial_controller.close()


run_vibe_server = start_vibe_ide


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser(description="m5-utah WebUSB Vibe Gateway (Feature 50)")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8023)
    parser.add_argument("--registry", default="registry/units.json")
    parser.add_argument("--telemetry-schema", default="schemas/telemetry.schema.json")
    parser.add_argument(
        "--serial",
        default=None,
        help="Optional host serial port for server-side injection (e.g. COM3)",
    )
    parser.add_argument("--baudrate", type=int, default=115200)
    args = parser.parse_args()
    start_vibe_ide(
        args.host,
        args.port,
        args.registry,
        args.telemetry_schema,
        serial_port=args.serial,
        baudrate=args.baudrate,
    )


if __name__ == "__main__":
    main()
