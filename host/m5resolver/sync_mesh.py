from __future__ import annotations

import logging
from typing import Any, Protocol

from .delta_engine import BitmappedDeltaCompiler, DeltaEncoder
from .graph_engine import StateGraphEngine

logger = logging.getLogger("m5resolver.sync_mesh")


class ClusterTransport(Protocol):
    def query_node_readiness(self, node_id: str, payload: dict[str, Any]) -> bool: ...

    def broadcast_commit_token(self, node_id: str, payload: dict[str, Any]) -> None: ...


class MeshStateSynchronizer:
    """
    Transactional multi-node mesh synchronization (2PC).

    Phase 1: pre-flight readiness query on every cluster node.
    Phase 2: simultaneous commit when all nodes approve.
    """

    def __init__(self, node_list: list[str]) -> None:
        self.nodes = list(node_list)
        self.cluster_registry: dict[str, dict[str, Any]] = {node: {} for node in self.nodes}

    @staticmethod
    def _estimate_buffer_demand(mutation: dict[str, Any]) -> int:
        units = mutation.get("units", {})
        if not isinstance(units, dict):
            return 512
        total = 0
        for config in units.values():
            if isinstance(config, dict):
                total += int(config.get("buffer_size_bytes", config.get("buffer_allocation_bytes", 256)))
        return max(total, 512)

    @staticmethod
    def validate_mutation_graph(mutation: dict[str, Any]) -> list[str]:
        units = mutation.get("units")
        if not isinstance(units, dict):
            return []
        graph = StateGraphEngine.from_units(units)
        return graph.validate_dag()

    def compile_commit_delta(
        self,
        mutation: dict[str, Any],
        *,
        changed_node: str | None = None,
        transaction_sequence_id: int = 1,
    ) -> bytes | None:
        units = mutation.get("units")
        if not isinstance(units, dict):
            return None
        if changed_node:
            return DeltaEncoder.encode_graph_mutation(
                units, changed_node, transaction_sequence_id=transaction_sequence_id
            )
        if len(units) == 1:
            name, config = next(iter(units.items()))
            if isinstance(config, dict):
                slot = int(config.get("slot_id", 0))
                freq = int(config.get("frequency_hz", 0))
                return BitmappedDeltaCompiler.compile_bitmap_delta(
                    slot, freq, transaction_sequence_id
                )
        return None

    def execute_cluster_mutation(
        self,
        cluster_intent_delta: dict[str, Any],
        transport: ClusterTransport,
    ) -> bool:
        logger.info("[MESH DETECTOR] Launching Phase 1: Pre-flight state verification...")

        graph_errors = self.validate_mutation_graph(cluster_intent_delta)
        if graph_errors:
            logger.error("[MESH ABORT] Graph validation failed: %s", graph_errors)
            return False

        prepare_payload = {
            **cluster_intent_delta,
            "requested_buffer_bytes": self._estimate_buffer_demand(cluster_intent_delta),
            "transaction_phase": "prepare",
        }

        agreed_nodes = 0
        for node in self.nodes:
            if transport.query_node_readiness(node, prepare_payload):
                agreed_nodes += 1
                logger.info(" -> Node '%s' approved allocation map alignment configuration.", node)
            else:
                logger.error(" -> Node '%s' rejected transaction. Aborting synchronization.", node)
                return False

        if agreed_nodes != len(self.nodes):
            return False

        logger.info("[MESH SUCCESS] Phase 2: Committing structural mutation across cluster trunk...")
        commit_payload = {
            **cluster_intent_delta,
            "transaction_phase": "commit",
            "transaction_commit": True,
        }
        units = cluster_intent_delta.get("units", {})
        for node in self.nodes:
            self.cluster_registry[node] = units if isinstance(units, dict) else {}
            transport.broadcast_commit_token(node, commit_payload)
        return True

    def registry_snapshot(self) -> dict[str, dict[str, Any]]:
        return dict(self.cluster_registry)


class ControllerClusterTransport:
    """Adapter binding MeshStateSynchronizer 2PC to IntentController serial I/O."""

    def __init__(self, controller: Any) -> None:
        self.controller = controller
        self.committed_nodes: list[str] = []

    def query_node_readiness(self, node_id: str, payload: dict[str, Any]) -> bool:
        if not getattr(self.controller, "is_open", False):
            return False
        prepare_intent = {
            "transaction_prepare": {
                "requested_buffer_bytes": payload.get("requested_buffer_bytes", 512),
                "transaction_id": node_id,
            }
        }
        errors = self.controller.send_intent(prepare_intent, stage=False)
        return not errors

    def broadcast_commit_token(self, node_id: str, payload: dict[str, Any]) -> None:
        if not getattr(self.controller, "is_open", False):
            return
        units = payload.get("units", {})
        commit_intent: dict[str, Any] = {
            "transaction_commit": True,
            "registry": {"units": units},
        }
        self.controller.send_intent(commit_intent, stage=False)
        self.committed_nodes.append(node_id)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    class DummyTransport:
        def query_node_readiness(self, node_id: str, payload: Any) -> bool:
            return True

        def broadcast_commit_token(self, node_id: str, payload: Any) -> None:
            pass

    synchronizer = MeshStateSynchronizer(node_list=["m5_node_01", "m5_node_02"])
    sample_mutation = {"units": {"dsp_worker": {"type": "virtual_dsp", "frequency_hz": 200}}}
    success = synchronizer.execute_cluster_mutation(sample_mutation, DummyTransport())
    print(f"Cluster State Synchronized: {success}")
