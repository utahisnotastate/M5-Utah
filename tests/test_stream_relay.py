import pytest

from m5resolver.stream_relay import (
    DEFAULT_CHUNK_BYTES,
    InPlaceTokenMirror,
    PIPE_FRAME_BINARY,
    PIPE_FRAME_JSON,
    StreamRelayEncoder,
)


def test_wrap_json_line_prefix():
    frame = StreamRelayEncoder.wrap_json_line('{"display":{"clear":true}}')
    assert frame[0] == PIPE_FRAME_JSON
    assert b"display" in frame


def test_wrap_binary_frame_prefix():
    frame = StreamRelayEncoder.wrap_binary_frame(b"\xde\xda\x01\x00\x00")
    assert frame[0] == PIPE_FRAME_BINARY
    assert frame[1:] == b"\xde\xda\x01\x00\x00"


def test_chunk_payload_splits_large_frames():
    payload = b"x" * 2500
    chunks = StreamRelayEncoder.chunk_payload(payload, max_chunk=1024)
    assert len(chunks) == 3
    assert sum(len(c) for c in chunks) == 2500


def test_split_in_place_token():
    key, value = StreamRelayEncoder.split_in_place_token(b"engine_target:pwm_driver")
    assert key == b"engine_target"
    assert value == b"pwm_driver"


def test_validate_frame_alignment_rejects_empty_chunk():
    errors = StreamRelayEncoder.validate_frame_alignment([b""])
    assert any("empty" in e for e in errors)


def test_in_place_token_mirror():
    tokens = InPlaceTokenMirror.tokenize(b"alpha:beta,gamma")
    assert tokens == [b"alpha", b"beta", b"gamma"]
