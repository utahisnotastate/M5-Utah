import json

from m5resolver.events import VirtualEventRouter


def test_virtual_event_router_multiplexes_subscribers():
    router = VirtualEventRouter()
    seen: list[dict] = []

    router.register_intent_pipe("button_click_event", lambda data: seen.append(data))
    router.register_intent_pipe("button_click_event", lambda data: seen.append({"echo": data.get("state")}))

    ok = router.ingest_hardware_signal(
        '{"event_type": "button_click_event", "payload": {"hardware_source_pin": 39, "state": "FALLING"}}'
    )

    assert ok is True
    assert len(seen) == 2
    assert seen[0]["hardware_source_pin"] == 39
    assert seen[1]["echo"] == "FALLING"


def test_virtual_event_router_hardware_event_alias():
    router = VirtualEventRouter()
    hits: list[str] = []
    router.register_intent_pipe("motion_spike_event", lambda data: hits.append(str(data.get("axis"))))

    packet = {"type": "hardware_event", "event_type": "motion_spike_event", "payload": {"axis": "x"}}
    assert router.ingest_packet(packet) is True
    assert hits == ["x"]


def test_virtual_event_router_default_button_patch():
    router = VirtualEventRouter()
    sent: list[dict] = []
    router.set_intent_sink(lambda intent: sent.append(intent))
    router.bind_default_routes()

    router.ingest_packet({"event_type": "button_click_event", "payload": {"state": "FALLING"}})

    assert sent
    assert sent[0]["power"]["led"] == 64


def test_virtual_event_router_ingest_mesh_signal():
    router = VirtualEventRouter()
    seen: list[float] = []
    router.register_intent_pipe("imu_tilt_event", lambda data: seen.append(data.get("magnitude")))

    line = '{"event_type": "imu_tilt_event", "payload": {"pin_source": 34, "magnitude": 2.5}}'
    assert router.ingest_mesh_signal(line) is True
    assert seen == [2.5]


def test_virtual_event_router_parse_stream_prefix():
    line = '[VIRTUAL_EVENT_STREAM]:{"event_type":"imu_tilt_event","payload":{"magnitude":1.0}}'
    parsed = VirtualEventRouter.parse_event_line(line)
    assert parsed is not None
    assert parsed["event_type"] == "imu_tilt_event"
