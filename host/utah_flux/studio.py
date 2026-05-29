from __future__ import annotations

import json
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from .bricks import catalog_for_api
from .compiler import compile_project
from .project import FluxProject
from .templates import get_template, list_templates

STATIC_DIR = Path(__file__).parent / "static"


class StudioHandler(BaseHTTPRequestHandler):
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

    def _send_bytes(self, status: int, content: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def do_OPTIONS(self) -> None:  # noqa: N802
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self) -> None:  # noqa: N802
        path = self.path.split("?", 1)[0]
        if path in ("/", "/index.html"):
            html = (STATIC_DIR / "index.html").read_text(encoding="utf-8")
            self._send_bytes(200, html.encode("utf-8"), "text/html; charset=utf-8")
            return
        if path.startswith("/static/"):
            asset = STATIC_DIR / path.replace("/static/", "", 1)
            if asset.exists():
                ctype = "text/css" if asset.suffix == ".css" else "application/javascript"
                self._send_bytes(200, asset.read_bytes(), ctype)
                return
        if path == "/api/bricks":
            self._send_json(200, {"bricks": catalog_for_api()})
            return
        if path == "/api/templates":
            self._send_json(200, {"templates": list_templates()})
            return
        if path.startswith("/api/templates/"):
            tid = path.rsplit("/", 1)[-1]
            project = get_template(tid)
            if project is None:
                self._send_json(404, {"error": "template_not_found"})
                return
            self._send_json(200, {"project": project})
            return
        if path == "/api/health":
            self._send_json(200, {"ok": True, "app": "utah-flux-studio"})
            return
        self._send_json(404, {"error": "not_found"})

    def do_POST(self) -> None:  # noqa: N802
        path = self.path.split("?", 1)[0]
        length = int(self.headers.get("Content-Length", "0"))
        data = json.loads(self.rfile.read(length).decode("utf-8")) if length else {}

        if path == "/api/compile":
            project = FluxProject.from_dict(data.get("project", {}))
            result = compile_project(project)
            self._send_json(200 if result["ok"] else 400, result)
            return

        self._send_json(404, {"error": "not_found"})


def start_studio(host: str = "127.0.0.1", port: int = 8765, open_browser: bool = True) -> ThreadingHTTPServer:
    server = ThreadingHTTPServer((host, port), StudioHandler)
    url = f"http://{host}:{port}"

    if open_browser:
        threading.Timer(0.6, lambda: webbrowser.open(url)).start()

    print(f"Utah Flux Studio is running at {url}")
    return server


def main() -> None:
    server = start_studio()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
