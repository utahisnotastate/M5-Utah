from __future__ import annotations

import asyncio
import json
import logging
import re
from pathlib import Path

from .hardware_matrix import HardwareMatrix

logger = logging.getLogger("utah_flux.utahclaw")

STATIC_DIR = Path(__file__).parent / "static"
STUDIO_HTML = STATIC_DIR / "utah_studio.html"
CLAW_HTML = STATIC_DIR / "claw_studio.html"

SYSTEM_PROMPT = """
[SYSTEM CONFIGURATION: UTAH-CLAW LOCAL AGENT]
You are UtahClaw, an intent-resolution agent for General 23 / m5-utah.
The user provides intent; you output strict JSON intents for M5Stack CoreS3 or corrected code.
If the user provides an ERROR LOG, output the CORRECTED CODE immediately without apology.
Do not use markdown fences. Output ONLY raw executable JSON or code.
"""

ERROR_PATTERN = re.compile(
    r"(Traceback|SyntaxError|Exception|ERROR|Guru Meditation|abort\(\)|panic)",
    re.IGNORECASE,
)


def _strip_markdown_fences(text: str) -> str:
    stripped = text.strip()
    if stripped.startswith("```"):
        lines = stripped.split("\n")
        if len(lines) >= 2:
            return "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
    return stripped


async def vibe_code_agent(matrix: HardwareMatrix, intent: str, *, is_error: bool = False) -> str:
    """Localized LLM vibe-coding via Ollama (offline, zero cloud API)."""
    try:
        import ollama
    except ImportError as exc:
        raise RuntimeError("UtahClaw requires ollama package: pip install -e 'host[claw]'") from exc

    prompt = f"Fix this device error log:\n{intent}" if is_error else f"Write m5-utah intent JSON to: {intent}"
    logger.info("[UTAH-CLAW] analyzing: %s", prompt[:120])

    response = await asyncio.to_thread(
        ollama.chat,
        model="llama3",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
    )
    generated = _strip_markdown_fences(response["message"]["content"])
    logger.info("[UTAH-CLAW] manifestation complete (%s bytes)", len(generated))

    if generated.startswith("{"):
        try:
            matrix.push_intent_json(json.loads(generated))
        except json.JSONDecodeError:
            matrix.push_code_paste_mode(generated)
    else:
        matrix.push_code_paste_mode(generated)
    return generated


def create_app():
    try:
        from fastapi import FastAPI, WebSocket
        from fastapi.responses import HTMLResponse
    except ImportError as exc:
        raise RuntimeError("pip install -e 'host[claw]'") from exc

    app = FastAPI(title="Utah-Flux Studio w/ UtahClaw")
    matrix = HardwareMatrix()

    @app.get("/")
    async def studio_gui():
        html_path = STUDIO_HTML if STUDIO_HTML.is_file() else CLAW_HTML
        if html_path.is_file():
            return HTMLResponse(content=html_path.read_text(encoding="utf-8"))
        return HTMLResponse(content="<h1>UtahClaw Studio</h1><p>static/utah_studio.html missing</p>")

    @app.get("/studio")
    async def studio_alias():
        return await studio_gui()

    @app.websocket("/ws/studio")
    async def websocket_studio(websocket: WebSocket):
        await websocket.accept()
        if matrix.connect():
            await websocket.send_text(
                json.dumps({"type": "agent", "data": f"Linked: {matrix.active_port}"})
            )
        else:
            await websocket.send_text(json.dumps({"type": "agent", "data": "Awaiting hardware..."}))

        async def read_serial_loop() -> None:
            while True:
                line = matrix.readline_text()
                if line:
                    discovery = matrix.ingest_line(line)
                    if discovery is not None:
                        await websocket.send_text(json.dumps({"type": "discovery", "data": discovery}))
                    else:
                        await websocket.send_text(json.dumps({"type": "log", "data": line}))

                    if ERROR_PATTERN.search(line):
                        await websocket.send_text(
                            json.dumps(
                                {
                                    "type": "agent",
                                    "data": f"Entropy detected. Auto-healing: {line[:200]}",
                                }
                            )
                        )
                        try:
                            await vibe_code_agent(matrix, line, is_error=True)
                            await websocket.send_text(
                                json.dumps({"type": "agent", "data": "Patch deployed."})
                            )
                        except Exception as exc:
                            await websocket.send_text(
                                json.dumps({"type": "agent", "data": f"Heal failed: {exc}"})
                            )
                await asyncio.sleep(0.01)

        async def read_gui_loop() -> None:
            while True:
                raw = await websocket.receive_text()
                payload = json.loads(raw)
                if payload.get("type") == "vibe_request":
                    await websocket.send_text(json.dumps({"type": "agent", "data": "Thinking..."}))
                    try:
                        code = await vibe_code_agent(matrix, str(payload.get("intent", "")))
                        await websocket.send_text(
                            json.dumps({"type": "agent", "data": f"Deployed:\n{code}"})
                        )
                    except Exception as exc:
                        await websocket.send_text(
                            json.dumps({"type": "agent", "data": f"Vibe failed: {exc}"})
                        )

        await asyncio.gather(read_serial_loop(), read_gui_loop())

    return app


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    try:
        import uvicorn
    except ImportError as exc:
        raise RuntimeError("pip install -e 'host[claw]'") from exc

    uvicorn.run(create_app(), host="127.0.0.1", port=8024)


if __name__ == "__main__":
    main()
