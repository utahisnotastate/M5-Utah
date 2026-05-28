from __future__ import annotations

import argparse
import json
import time

from .controller import IntentController


def main() -> None:
    parser = argparse.ArgumentParser(description="M5 Resolver host CLI")
    parser.add_argument("--port", required=True, help="Serial port (e.g. COM3 or /dev/ttyUSB0)")
    parser.add_argument("--baud", type=int, default=115200)
    parser.add_argument("--watch", action="store_true", help="Stream telemetry")
    parser.add_argument("--intent", help="Raw JSON intent payload")
    args = parser.parse_args()

    ctl = IntentController(port=args.port, baud=args.baud)
    ctl.open()
    try:
        if args.intent:
            ctl.send_intent(json.loads(args.intent))
            time.sleep(0.1)

        if args.watch:
            while True:
                frame = ctl.read_frame()
                if frame:
                    print(frame.raw)
    except KeyboardInterrupt:
        pass
    finally:
        ctl.close()


if __name__ == "__main__":
    main()
