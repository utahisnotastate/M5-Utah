from __future__ import annotations

import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from .agent import AgenticController
from .registry_ops import RegistryStore
from .vibe_compiler import compile_vibe_to_intent
from .validation import validate_intent_payload
from .safety import validate_intent_safety

STATIC_DIR = Path(__file__).parent / "static"


class VibeHandler(BaseHTTPRequestHandler):
    registry_store: RegistryStore
    agent: AgenticController

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A003
        return

    def _send_json(self, status: int, payload: dict[str, Any]) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self) -> None:  # noqa: N802
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self) -> None:  # noqa: N802
        if self.path in ("/", "/index.html"):
            html = (STATIC_DIR / "vibe-ide.html").read_text(encoding="utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(html.encode("utf-8"))
            return
        if self.path == "/health":
            self._send_json(200, {"ok": True, "service": "vibe-ide"})
            return
        if self.path == "/registry":
            self._send_json(200, self.registry_store.load_raw())
            return
        self._send_json(404, {"error": "not_found"})

    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/generate_intent":
            self._send_json(404, {"error": "not_found"})
            return

        length = int(self.headers.get("Content-Length", "0"))
        data = json.loads(self.rfile.read(length).decode("utf-8"))
        prompt = data.get("prompt", "")
        dry_run = bool(data.get("dry_run", False))

        intent = compile_vibe_to_intent(prompt)
        errors = (
            validate_intent_payload(intent)
            + validate_intent_safety(intent)
            + self.agent.stage_intent(intent)
        )
        if errors:
            self._send_json(400, {"errors": errors})
            return

        if "registry" in intent:
            reg_errors = self.registry_store.merge_runtime_units(
                intent["registry"].get("units", {})
            )
            if reg_errors:
                self._send_json(400, {"errors": reg_errors})
                return

        if dry_run:
            self._send_json(200, {"intent": intent, "dry_run": True})
            return

        self._send_json(200, {"intent": intent, "dry_run": False})


def start_vibe_ide(
    host: str = "127.0.0.1",
    port: int = 8023,
    registry_path: str = "registry/units.json",
    telemetry_schema_path: str = "schemas/telemetry.schema.json",
) -> None:
    registry_store = RegistryStore(registry_path)
    agent = AgenticController(registry_path, telemetry_schema_path)

    handler = VibeHandler
    handler.registry_store = registry_store
    handler.agent = agent

    server = ThreadingHTTPServer((host, port), handler)
    print(f"[*] m5-utah Vibe-IDE running at http://{host}:{port}")
    print("[*] Open in Chrome/Edge and connect device via WebSerial")
    server.serve_forever()


def main() -> None:
    parser = argparse.ArgumentParser(description="m5-utah Vibe IDE server")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8023)
    parser.add_argument("--registry", default="registry/units.json")
    parser.add_argument("--telemetry-schema", default="schemas/telemetry.schema.json")
    args = parser.parse_args()
    start_vibe_ide(args.host, args.port, args.registry, args.telemetry_schema)


if __name__ == "__main__":
    main()
