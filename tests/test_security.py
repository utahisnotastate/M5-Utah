from m5resolver.security import intent_content_digest, sign_intent, verify_intent_signature


def test_sign_and_verify_round_trip():
    intent = {"registry": {"units": {"sensor": {"frequency_hz": 4}}}}
    signed = sign_intent(intent, timestamp_epoch=1700000000)
    assert "security" in signed
    assert len(signed["security"]["signature_hex"]) == 64
    assert verify_intent_signature(signed) == []


def test_digest_is_deterministic():
    intent = {"display": {"clear": True}, "power": {"led": 8}}
    assert intent_content_digest(intent) == intent_content_digest(intent)
