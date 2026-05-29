from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from .binwire import BINWIRE_FRAME_LEN, BinwireEncoder
from .controller import IntentController
from .security import sign_intent, verify_intent_signature
from .validation import validate_intent_payload


def main() -> None:
    parser = argparse.ArgumentParser(description="M5 Resolver host CLI")
    parser.add_argument("--port", required=True, help="Serial port (e.g. COM3 or /dev/ttyUSB0)")
    parser.add_argument("--baud", type=int, default=115200)
    parser.add_argument("--watch", action="store_true", help="Stream telemetry")
    parser.add_argument("--intent", help="Raw JSON intent payload")
    parser.add_argument("--intent-file", help="Path to JSON file containing intent payload")
    parser.add_argument("--dry-run", action="store_true", help="Validate payload only, do not send")
    parser.add_argument(
        "--fastpath",
        action="store_true",
        help="Validate JSON intent then send binwire fast-path binary frame",
    )
    parser.add_argument(
        "--sign",
        action="store_true",
        help="Attach SHA-256 security.signature_hex before sending intent",
    )
    parser.add_argument(
        "--require-registry-signature",
        action="store_true",
        help="Reject registry intents missing security.signature_hex",
    )
    args = parser.parse_args()

    intent_payload = _load_intent(args.intent, args.intent_file)
    if intent_payload is not None:
        if args.sign:
            intent_payload = sign_intent(intent_payload)
        errors = validate_intent_payload(
            intent_payload, require_registry_signature=args.require_registry_signature
        )
        if errors:
            for err in errors:
                print(f"validation_error: {err}")
            raise SystemExit(2)

    if args.dry_run:
        if intent_payload is None:
            print("dry_run_ok: no intent supplied")
        else:
            print("dry_run_ok: intent validated")
            if args.fastpath:
                frame = BinwireEncoder.encode_intent(intent_payload)
                if frame is None:
                    print("dry_run_error: intent has no binwire encodable fields")
                    raise SystemExit(2)
                print(f"dry_run_ok: binwire frame ({BINWIRE_FRAME_LEN} bytes) hex={frame.hex()}")
        return

    ctl = IntentController(
        port=args.port,
        baud=args.baud,
        sign_intents=args.sign,
        require_registry_signature=args.require_registry_signature,
    )
    ctl.open()
    try:
        if intent_payload is not None:
            if args.fastpath:
                frame = BinwireEncoder.encode_intent(intent_payload)
                if frame is None:
                    print("fastpath_error: intent has no binwire encodable fields")
                    raise SystemExit(2)
                ctl.send_fastpath(frame)
            else:
                ctl.send_intent(intent_payload)
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


def _load_intent(intent_raw: str | None, intent_file: str | None) -> dict | None:
    if intent_raw and intent_file:
        raise SystemExit("Use either --intent or --intent-file, not both.")
    if intent_raw:
        return json.loads(intent_raw)
    if intent_file:
        payload = Path(intent_file).read_text(encoding="utf-8")
        return json.loads(payload)
    return None


if __name__ == "__main__":
    main()
