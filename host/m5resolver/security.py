from __future__ import annotations

import hashlib
import json
import time
from typing import Any

SECURITY_ALGORITHM = "sha256-canonical-v1"


def canonical_intent_bytes(intent: dict[str, Any]) -> bytes:
    body = {k: v for k, v in intent.items() if k != "security"}
    return json.dumps(body, sort_keys=True, separators=(",", ":")).encode("utf-8")


def intent_content_digest(intent: dict[str, Any]) -> str:
    return hashlib.sha256(canonical_intent_bytes(intent)).hexdigest()


def sign_intent(intent: dict[str, Any], *, timestamp_epoch: int | None = None) -> dict[str, Any]:
    """Attach a SHA-256 digest over the canonical intent body (excluding security)."""
    signed = dict(intent)
    signed.pop("security", None)
    digest = intent_content_digest(signed)
    signed["security"] = {
        "algorithm": SECURITY_ALGORITHM,
        "signature_hex": digest,
        "timestamp_epoch": int(time.time() if timestamp_epoch is None else timestamp_epoch),
    }
    return signed


def verify_intent_signature(intent: dict[str, Any]) -> list[str]:
    security = intent.get("security")
    if security is None:
        return []

    if not isinstance(security, dict):
        return ["security must be an object"]

    signature = security.get("signature_hex")
    if not isinstance(signature, str) or not signature:
        return ["security.signature_hex is required when security block is present"]

    algorithm = security.get("algorithm", SECURITY_ALGORITHM)
    if algorithm != SECURITY_ALGORITHM:
        return [f"unsupported security algorithm: {algorithm}"]

    body = {k: v for k, v in intent.items() if k != "security"}
    expected = intent_content_digest(body)
    if signature != expected:
        return ["security.signature_hex mismatch: intent payload corrupted or tampered"]

    ts = security.get("timestamp_epoch")
    if ts is not None and not isinstance(ts, int):
        return ["security.timestamp_epoch must be an integer"]

    return []


def require_signature_for_registry(intent: dict[str, Any], *, enabled: bool) -> list[str]:
    if not enabled:
        return []
    if "registry" in intent and "security" not in intent:
        return ["registry mutations require security.signature_hex in secure mesh mode"]
    return []
