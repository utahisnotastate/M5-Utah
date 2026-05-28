from __future__ import annotations

import argparse
import time

from m5resolver import ContinuousWire, FluxGraph, IntentController


def clamp_frequency(v: float) -> float:
    hz = 440.0 + (abs(v) * 180.0)
    return max(220.0, min(1800.0, hz))


def main() -> None:
    parser = argparse.ArgumentParser(description="Map accel.x to tone frequency")
    parser.add_argument("--port", required=True)
    parser.add_argument("--baud", type=int, default=115200)
    args = parser.parse_args()

    graph = FluxGraph()
    graph.add_wire(ContinuousWire("accel.x", ("speaker", "tone", "frequency"), clamp_frequency))
    graph.add_wire(ContinuousWire("accel.x", ("speaker", "tone", "duration"), lambda _: 50))
    graph.add_wire(ContinuousWire("accel.x", ("speaker", "tone", "channel"), lambda _: 0))
    graph.add_wire(
        ContinuousWire(
            "accel.x",
            ("display", "text", "payload"),
            lambda x: f"accel.x={x:.3f}",
        )
    )
    graph.add_wire(ContinuousWire("accel.x", ("display", "text", "x"), lambda _: 8))
    graph.add_wire(ContinuousWire("accel.x", ("display", "text", "y"), lambda _: 24))
    graph.add_wire(ContinuousWire("accel.x", ("display", "text", "size"), lambda _: 2))
    graph.add_wire(ContinuousWire("accel.x", ("display", "text", "color"), lambda _: 0xFFFF))
    graph.add_wire(ContinuousWire("accel.x", ("display", "clear"), lambda _: True))
    graph.add_wire(ContinuousWire("accel.x", ("display", "bg_color"), lambda _: 0x0000))

    ctl = IntentController(port=args.port, baud=args.baud)
    ctl.open()
    try:
        while True:
            frame = ctl.read_frame()
            if not frame:
                continue
            if frame.payload.get("type") != "telemetry":
                continue

            patch = graph.resolve_intent_patch(frame.payload)
            if patch:
                ctl.send_intent(patch)
            time.sleep(0.003)
    except KeyboardInterrupt:
        pass
    finally:
        ctl.close()


if __name__ == "__main__":
    main()
