from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path

from .hardware_matrix import HardwareMatrix

logger = logging.getLogger("utah_flux.omniscient")

STATIC_DIR = Path(__file__).parent / "static"
OMNISCIENT_HTML = STATIC_DIR / "omniscient.html"


def create_app():
    try:
        from fastapi import FastAPI, WebSocket
        from fastapi.responses import HTMLResponse
    except ImportError as exc:
        raise RuntimeError(
            "Omniscient daemon requires fastapi and uvicorn. "
            "Install with: pip install -e 'host[daemon]'"
        ) from exc

    app = FastAPI(title="Utah-Flux Omniscient OS")
    matrix = HardwareMatrix()

    @app.get("/api/health")
    async def health() -> dict:
        linked = matrix.serial_conn is not None and getattr(matrix.serial_conn, "is_open", False)
        return {
            "ok": True,
            "app": "utah-flux-omniscient",
            "linked": linked,
            "port": matrix.active_port,
            "units": matrix.connected_units,
        }

    @app.get("/")
    async def get_ultimate_gui():
        if OMNISCIENT_HTML.is_file():
            return HTMLResponse(content=OMNISCIENT_HTML.read_text(encoding="utf-8"))
        return HTMLResponse(content="<h1>Utah-Flux Omniscient OS</h1><p>static/omniscient.html missing</p>")

    @app.websocket("/ws/telemetry")
    async def websocket_endpoint(websocket: WebSocket):
        await websocket.accept()

        if not matrix.connect():
            await websocket.send_text(json.dumps({"status": "AWAITING_HARDWARE"}))
        else:
            await websocket.send_text(
                json.dumps(
                    {
                        "status": "IMMORTAL_KERNEL_LINKED",
                        "port": matrix.active_port,
                    }
                )
            )

        try:
            while True:
                line = matrix.readline_text()
                if line:
                    discovery = matrix.ingest_line(line)
                    if discovery is not None:
                        await websocket.send_text(json.dumps(discovery))
                    elif line.startswith("{"):
                        await websocket.send_text(line)
                await asyncio.sleep(0.05)
        except Exception as exc:
            logger.warning("websocket severed: %s", exc)

    return app


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    try:
        import uvicorn
    except ImportError as exc:
        raise RuntimeError("pip install -e 'host[daemon]'") from exc

    app = create_app()
    uvicorn.run(app, host="127.0.0.1", port=8000)


if __name__ == "__main__":
    main()
