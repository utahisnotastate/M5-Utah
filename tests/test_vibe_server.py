import json
import struct
import threading
from http.client import HTTPConnection

from m5resolver.vibe_compiler import compile_vibe_to_intent
from m5resolver.vibe_pipeline import compile_vibe_wire_payload
from m5resolver.vibe_server import VibeGatewayHandler
from http.server import ThreadingHTTPServer


def test_vibe_compiler_gpio_fast_track():
    intent = compile_vibe_to_intent("Blink GPIO pin 10 at 50Hz frequency mask")
    assert intent["intent"]["action"] == "fast_track_gpio"
    assert intent["intent"]["parameters"]["pin"] == 10
    assert intent["intent"]["parameters"]["frequency_hz"] == 50
    assert intent["fastpath"] is True


def test_vibe_pipeline_emits_binwire_for_gpio_prompt():
    result = compile_vibe_wire_payload(
        "blink gpio pin 10 at 50hz",
        stage=False,
    )
    assert result.ok
    assert result.wire_format == "fastpath"
    assert result.payload is not None
    assert result.payload.startswith(b"\x23\x23")
    assert len(result.payload) == 10

    unit_id, pin, freq, state = struct.unpack("!BBHI", result.payload[2:])
    assert pin == 10
    assert freq == 50


def test_compile_vibe_http_endpoint():
    from m5resolver.agent import AgenticController
    from m5resolver.registry_ops import RegistryStore
    from m5resolver.resource_orchestrator import HostResourceOrchestrator

    registry_store = RegistryStore("registry/units.json")
    agent = AgenticController("registry/units.json", "schemas/telemetry.schema.json")
    orchestrator = HostResourceOrchestrator()

    handler = VibeGatewayHandler
    handler.registry_store = registry_store
    handler.agent = agent
    handler.orchestrator = orchestrator
    handler.serial_controller = None

    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    try:
        conn = HTTPConnection("127.0.0.1", port, timeout=5)
        body = json.dumps({"prompt": "blink gpio pin 10 at 50hz"})
        conn.request(
            "POST",
            "/compile_vibe",
            body=body,
            headers={"Content-Type": "application/json"},
        )
        response = conn.getresponse()
        assert response.status == 200
        assert response.getheader("Content-Type") == "application/octet-stream"
        assert response.getheader("X-Wire-Format") == "fastpath"
        payload = response.read()
        assert payload.startswith(b"\x23\x23")
        assert len(payload) == 10
        conn.close()
    finally:
        server.shutdown()
