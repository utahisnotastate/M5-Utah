from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable


Transform = Callable[[Any], Any]


@dataclass
class ContinuousWire:
    source_key: str
    sink_path: tuple[str, ...]
    transform: Transform = lambda x: x
    _cached_value: Any = field(default=None, init=False, repr=False)

    def route(self, source_value: Any) -> tuple[Any, bool]:
        mapped = self.transform(source_value)
        if mapped != self._cached_value:
            self._cached_value = mapped
            return mapped, True
        return None, False


class MeshBus:
    """Lightweight gossip bus for sharing registry/intent state across peers."""

    def __init__(self) -> None:
        self._peers: dict[str, dict[str, Any]] = {}
        self._state: dict[str, Any] = {}

    def announce(self, peer_id: str, payload: dict[str, Any]) -> None:
        self._peers[peer_id] = payload
        self._state.update(payload)

    def gossip_merge(self) -> dict[str, Any]:
        merged: dict[str, Any] = {}
        for peer_payload in self._peers.values():
            merged.update(peer_payload)
        self._state = merged
        return merged

    @property
    def state(self) -> dict[str, Any]:
        return dict(self._state)


class FluxGraph:
    """Applies wire mappings from telemetry to intent patches."""

    def __init__(self, mesh: MeshBus | None = None) -> None:
        self._wires: list[ContinuousWire] = []
        self.mesh = mesh or MeshBus()

    def add_wire(self, wire: ContinuousWire) -> None:
        self._wires.append(wire)

    def resolve_intent_patch(self, telemetry: dict[str, Any]) -> dict[str, Any]:
        patch: dict[str, Any] = {}
        for wire in self._wires:
            value = _read_key(telemetry, wire.source_key)
            if value is None:
                continue
            mapped, changed = wire.route(value)
            if not changed:
                continue
            _write_path(patch, wire.sink_path, mapped)
        return patch


def _read_key(payload: dict[str, Any], key: str) -> Any:
    if "." not in key:
        return payload.get(key)
    node: Any = payload
    for part in key.split("."):
        if not isinstance(node, dict):
            return None
        node = node.get(part)
        if node is None:
            return None
    return node


def _write_path(payload: dict[str, Any], path: tuple[str, ...], value: Any) -> None:
    node = payload
    for part in path[:-1]:
        child = node.get(part)
        if not isinstance(child, dict):
            child = {}
            node[part] = child
        node = child
    node[path[-1]] = value
