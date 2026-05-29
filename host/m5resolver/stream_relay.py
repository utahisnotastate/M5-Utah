from __future__ import annotations

import struct
from typing import Iterable

PIPE_FRAME_JSON = 0x01
PIPE_FRAME_BINARY = 0x02
RING_MAX_FRAME_BYTES = 8180
DEFAULT_CHUNK_BYTES = 1024


class StreamRelayEncoder:
    """Host-side frame wrapper aligned with firmware CrossCorePipe ring items."""

    @staticmethod
    def wrap_json_line(line: str) -> bytes:
        payload = line.encode("utf-8")
        if len(payload) > RING_MAX_FRAME_BYTES:
            raise ValueError(f"json line exceeds ring frame limit ({RING_MAX_FRAME_BYTES} bytes)")
        return bytes([PIPE_FRAME_JSON]) + payload

    @staticmethod
    def wrap_binary_frame(frame: bytes) -> bytes:
        if len(frame) > RING_MAX_FRAME_BYTES:
            raise ValueError(f"binary frame exceeds ring frame limit ({RING_MAX_FRAME_BYTES} bytes)")
        return bytes([PIPE_FRAME_BINARY]) + frame

    @staticmethod
    def chunk_payload(payload: bytes, *, max_chunk: int = DEFAULT_CHUNK_BYTES) -> list[bytes]:
        if max_chunk <= 0:
            raise ValueError("max_chunk must be positive")
        return [payload[i : i + max_chunk] for i in range(0, len(payload), max_chunk)]

    @staticmethod
    def split_in_place_token(raw: bytes, delimiter: int = ord(":")) -> tuple[bytes, bytes]:
        buf = bytearray(raw)
        index = buf.find(delimiter)
        if index == -1:
            raise ValueError("delimiter not found in token buffer")
        buf[index] = 0
        key = bytes(buf[:index])
        value = bytes(buf[index + 1 :]).strip(b"\x00")
        return key, value

    @staticmethod
    def validate_frame_alignment(frames: Iterable[bytes]) -> list[str]:
        errors: list[str] = []
        for idx, frame in enumerate(frames):
            if not frame:
                errors.append(f"chunk {idx} is empty")
                continue
            if len(frame) > RING_MAX_FRAME_BYTES + 1:
                errors.append(f"chunk {idx} exceeds ring buffer slot size")
        return errors


class InPlaceTokenMirror:
    """Python mirror of firmware InPlaceTokenizer delimiter mutation."""

    @staticmethod
    def tokenize(raw: bytes, delimiters: bytes = b",:") -> list[bytes]:
        buf = bytearray(raw)
        if not buf:
            return []

        starts = [0]
        for i, ch in enumerate(buf):
            if ch in delimiters:
                buf[i] = 0
                if i + 1 < len(buf):
                    starts.append(i + 1)

        tokens: list[bytes] = []
        for idx, start in enumerate(starts):
            end = starts[idx + 1] - 1 if idx + 1 < len(starts) else len(buf)
            part = bytes(buf[start:end]).split(b"\x00")[0]
            if part:
                tokens.append(part)
        return tokens
