from __future__ import annotations

import json
import logging
from typing import Any, Callable

logger = logging.getLogger("m5resolver.events")

VIRTUAL_EVENT_STREAM_PREFIX = "[VIRTUAL_EVENT_STREAM]:"

EventCallback = Callable[[dict[str, Any]], None]


class VirtualEventRouter:
    """
    Asymmetric virtual event routing (Feature 59).

    Decouples raw hardware signals from output targets; pipes filtered telemetry
    events into intent callbacks without firmware recompile.
    """

    def __init__(self) -> None:
        self.event_bindings: dict[str, list[EventCallback]] = {}
        self._default_intent_sink: Callable[[dict[str, Any]], None] | None = None

    def set_intent_sink(self, sink: Callable[[dict[str, Any]], None]) -> None:
        self._default_intent_sink = sink

    def register_intent_pipe(self, source_event: str, callback_action: EventCallback) -> None:
        """Bind a fluid soft-logic route to a dynamic telemetry trigger."""
        self.event_bindings.setdefault(source_event, []).append(callback_action)
        logger.info("[EVENT PIPE] Established dynamic route mapping for: '%s'", source_event)

    def unregister_event(self, source_event: str) -> None:
        self.event_bindings.pop(source_event, None)

    @staticmethod
    def parse_event_line(line: str) -> dict[str, Any] | None:
        payload_text = line.strip()
        if payload_text.startswith(VIRTUAL_EVENT_STREAM_PREFIX):
            payload_text = payload_text[len(VIRTUAL_EVENT_STREAM_PREFIX) :].strip()
        if not payload_text.startswith("{"):
            return None
        try:
            return json.loads(payload_text)
        except json.JSONDecodeError:
            return None

    def ingest_mesh_signal(self, raw_packet: str | dict[str, Any]) -> bool:
        """Process dynamic input flags from physical nodes or gossip mesh."""
        if isinstance(raw_packet, dict):
            return self.ingest_packet(raw_packet)
        return self.ingest_hardware_signal(raw_packet)

    def ingest_hardware_signal(self, raw_telemetry_packet: str) -> bool:
        try:
            packet = json.loads(raw_telemetry_packet)
        except json.JSONDecodeError:
            logger.error("Failed to decode raw inbound structural event string.")
            return False
        return self.ingest_packet(packet)

    def ingest_packet(self, packet: dict[str, Any]) -> bool:
        event_trigger = packet.get("event_type")
        if not event_trigger:
            if packet.get("type") == "hardware_event":
                event_trigger = packet.get("event")
            elif "event" in packet:
                event_trigger = packet.get("event")

        if not event_trigger:
            return False

        metadata = packet.get("payload", packet.get("event_payload", {}))
        if not isinstance(metadata, dict):
            metadata = {"value": metadata}

        subscribers = self.event_bindings.get(str(event_trigger), [])
        if not subscribers:
            logger.debug("Dropped unmapped environmental event frame: %s", event_trigger)
            return False

        logger.info(
            "[ROUTER] Multiplexing event '%s' down %s registered execution channels...",
            event_trigger,
            len(subscribers),
        )
        for subscriber in subscribers:
            subscriber(metadata)
        return True

    def bind_default_routes(self) -> None:
        """Common vibe routes: button -> LED toggle intent patch."""
        self.register_intent_pipe("button_click_event", self._button_to_led_patch)
        self.register_intent_pipe("motion_spike_event", self._motion_alert_patch)
        self.register_intent_pipe("imu_tilt_event", self._imu_tilt_patch)

    def _button_to_led_patch(self, data: dict[str, Any]) -> None:
        if self._default_intent_sink:
            state = str(data.get("state", "HIGH"))
            brightness = 64 if state in ("HIGH", "FALLING", "pressed") else 8
            self._default_intent_sink({"power": {"led": brightness}})

    def _motion_alert_patch(self, data: dict[str, Any]) -> None:
        if self._default_intent_sink:
            self._default_intent_sink(
                {
                    "display": {
                        "clear": True,
                        "text": {
                            "x": 8,
                            "y": 40,
                            "size": 2,
                            "color": 0xF800,
                            "payload": "Motion!",
                        },
                    },
                    "speaker": {"tone": {"frequency": 880, "duration": 60, "channel": 0}},
                }
            )

    def _imu_tilt_patch(self, data: dict[str, Any]) -> None:
        if not self._default_intent_sink:
            return
        magnitude = data.get("magnitude", 0)
        pin = data.get("pin_source", 0)
        self._default_intent_sink(
            {
                "display": {
                    "text": {
                        "x": 8,
                        "y": 56,
                        "size": 1,
                        "color": 0x07E0,
                        "payload": f"Tilt pin {pin} @ {magnitude:.2f}",
                    }
                }
            }
        )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    router = VirtualEventRouter()
    router.register_intent_pipe(
        "imu_tilt_event",
        lambda data: print(f"[ACTION] Triggering high-speed override update: {data}"),
    )
    router.ingest_mesh_signal(
        '{"event_type": "imu_tilt_event", "payload": {"pin_source": 21, "magnitude": 9.8}}'
    )
