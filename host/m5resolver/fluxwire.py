from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from .consensus import HardwareConsensusCluster
from .ecc_codec import TelemetryECC
from .stream_relay import StreamRelayEncoder
from .vector_clock import VectorClockTracker

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

    def __init__(
        self,
        mesh: MeshBus | None = None,
        gossip_mesh: Any | None = None,
        consensus: HardwareConsensusCluster | None = None,
        vector_clock: VectorClockTracker | None = None,
        *,
        host_id: str | None = None,
        enable_ecc_repair: bool = True,
    ) -> None:
        self._wires: list[ContinuousWire] = []
        self.mesh = mesh or MeshBus()
        self.gossip_mesh = gossip_mesh
        self.consensus = consensus
        self.enable_ecc_repair = enable_ecc_repair
        self.vector_clock = vector_clock or (
            VectorClockTracker(host_id) if host_id else None
        )
        self._pending_causal_reorder: list[dict[str, Any]] = []

    def attach_vector_clock(self, tracker: VectorClockTracker) -> None:
        self.vector_clock = tracker

    def ingest_telemetry_causality(self, telemetry: dict[str, Any]) -> bool:
        """Verify causal ordering; buffer out-of-order frames for re-sequencing."""
        if self.vector_clock is None:
            return True

        vectors = telemetry.get("vector_clocks")
        if not isinstance(vectors, dict):
            return True

        sender = str(telemetry.get("sender_id", "unknown"))
        if self.vector_clock.merge_and_verify_causality(
            {k: int(v) for k, v in vectors.items()}, sender
        ):
            self._flush_pending_causal()
            return True

        self._pending_causal_reorder.append(telemetry)
        return False

    def _flush_pending_causal(self) -> None:
        if not self.vector_clock or not self._pending_causal_reorder:
            return
        still_pending: list[dict[str, Any]] = []
        for frame in self._pending_causal_reorder:
            vectors = frame.get("vector_clocks", {})
            sender = str(frame.get("sender_id", "unknown"))
            if isinstance(vectors, dict) and self.vector_clock.merge_and_verify_causality(
                {k: int(v) for k, v in vectors.items()}, sender
            ):
                continue
            still_pending.append(frame)
        self._pending_causal_reorder = still_pending

    def stamp_outbound_event(self, payload: dict[str, Any]) -> dict[str, Any]:
        if self.vector_clock is None:
            return payload
        return self.vector_clock.stamp_event(payload)

    def attach_consensus(self, consensus: HardwareConsensusCluster) -> None:
        self.consensus = consensus

    def commit_cluster_registry(self, intent: dict[str, Any], *, term: int | None = None) -> bool:
        """Gate registry mutations through Raft leader authorization."""
        if self.consensus is None:
            return True
        if not self.consensus.is_leader:
            self.consensus.tick()
            return False
        committed = self.consensus.commit_registry_intent(intent, term=term)
        if committed:
            self.propagate_committed_registry(intent)
        return committed

    def propagate_committed_registry(self, intent: dict[str, Any]) -> None:
        registry = intent.get("registry")
        if not isinstance(registry, dict):
            return
        node_id = self.consensus.node_id if self.consensus else "local"
        self.mesh.announce(node_id, registry)
        if self.gossip_mesh is not None:
            self.gossip_mesh.update_local_registry(registry)
            self.gossip_mesh.broadcast_registry_gossip(registry)

    def add_wire(self, wire: ContinuousWire) -> None:
        self._wires.append(wire)

    def publish_telemetry(self, telemetry: dict[str, Any]) -> None:
        """Share telemetry status with gossip peers."""
        if self.gossip_mesh is None:
            return
        status = telemetry.get("status", "operational")
        self.gossip_mesh.update_local_status(str(status))
        if status in ("degraded", "error"):
            self.gossip_mesh.broadcast_registry_gossip(
                {"alert": "degraded_state", "telemetry": telemetry}
            )

    def repair_telemetry(self, telemetry: dict[str, Any]) -> tuple[dict[str, Any], bool]:
        if not self.enable_ecc_repair:
            return telemetry, False
        return TelemetryECC.repair_telemetry_payload(telemetry)

    def resolve_intent_patch(self, telemetry: dict[str, Any]) -> dict[str, Any]:
        telemetry, _ = self.repair_telemetry(telemetry)
        if not self.ingest_telemetry_causality(telemetry):
            return {}

        self.publish_telemetry(telemetry)
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

    def validate_relay_patch(self, patch: dict[str, Any]) -> list[str]:
        """Ensure a fluxwire patch fits firmware ring-buffer frame boundaries."""
        import json

        if not patch:
            return []
        line = json.dumps(patch, separators=(",", ":"))
        wrapped = StreamRelayEncoder.wrap_json_line(line)
        return StreamRelayEncoder.validate_frame_alignment(
            StreamRelayEncoder.chunk_payload(wrapped)
        )


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
