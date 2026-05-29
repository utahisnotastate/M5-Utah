from __future__ import annotations

import argparse
import time
from pathlib import Path

from m5resolver import ContinuousWire, FluxGraph, IntentController


def main() -> None:
    parser = argparse.ArgumentParser(description="Agentic closed-loop controller")
    parser.add_argument("--port", required=True)
    parser.add_argument("--registry", default="registry/units.json")
    parser.add_argument("--telemetry-schema", default="schemas/telemetry.schema.json")
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    graph = FluxGraph()
    graph.add_wire(ContinuousWire("accel.x", ("display", "text", "payload"), lambda x: f"x={x:.3f}"))

    ctl = IntentController(
        port=args.port,
        registry_path=str(root / args.registry),
        telemetry_schema_path=str(root / args.telemetry_schema),
        enable_agent=True,
    )
    ctl.flux = graph
    ctl.open()
    try:
        while True:
            ctl.read_frame()
            time.sleep(0.005)
    except KeyboardInterrupt:
        pass
    finally:
        ctl.close()


if __name__ == "__main__":
    main()
