from __future__ import annotations

import logging
import time
from typing import Any, Callable

logger = logging.getLogger("m5resolver.consensus")

VoteRpc = Callable[[str, int, str], bool]


class RaftNodeState:
    FOLLOWER = 0
    CANDIDATE = 1
    LEADER = 2


class HardwareConsensusCluster:
    """
    Lightweight Raft-inspired consensus for distributed registry mutations.

    Only the elected leader may commit cluster-wide registry changes; followers
    mirror the committed log as hot standbys.
    """

    def __init__(
        self,
        node_id: str,
        peers: list[str],
        *,
        vote_rpc: VoteRpc | None = None,
        election_timeout_s: float = 5.0,
    ) -> None:
        self.node_id = node_id
        self.peers = list(peers)
        self.current_term = 0
        self.role = RaftNodeState.FOLLOWER
        self.voted_for: str | None = None
        self.registry_log: list[dict[str, Any]] = []
        self.commit_index = 0
        self._last_heartbeat = time.monotonic()
        self._election_timeout_s = election_timeout_s
        self._vote_rpc = vote_rpc or self._default_grant_vote

    @staticmethod
    def _default_grant_vote(peer: str, term: int, candidate: str) -> bool:
        logger.debug("[CONSENSUS RPC] %s granted vote to %s for term %s", peer, candidate, term)
        return True

    @property
    def is_leader(self) -> bool:
        return self.role == RaftNodeState.LEADER

    def initiate_election(self) -> bool:
        """Trigger leader election when the current leader is unreachable."""
        self.current_term += 1
        self.role = RaftNodeState.CANDIDATE
        self.voted_for = self.node_id
        logger.warning(
            "[CONSENSUS] Node %s declared election for term %s", self.node_id, self.current_term
        )

        votes = 1
        for peer in self.peers:
            if self._vote_rpc(peer, self.current_term, self.node_id):
                votes += 1

        quorum = (len(self.peers) + 1) // 2
        if votes > quorum:
            self.role = RaftNodeState.LEADER
            self._last_heartbeat = time.monotonic()
            logger.info(
                "[CONSENSUS] Node %s elected LEADER for term %s", self.node_id, self.current_term
            )
            return True
        self.role = RaftNodeState.FOLLOWER
        return False

    def append_registry_intent(self, term: int, intent_mutation: dict[str, Any]) -> bool:
        """Append a registry mutation to the replicated log if the term is current."""
        if term < self.current_term:
            logger.error("[REJECTION] Outdated configuration term intercepted.")
            return False
        if term > self.current_term:
            self.current_term = term
            self.voted_for = None

        entry = {
            "term": term,
            "index": len(self.registry_log) + 1,
            "mutation": intent_mutation,
            "ts": time.time(),
        }
        self.registry_log.append(entry)
        logger.info("[LOG APPENDED] State mutation index %s secured.", entry["index"])
        return True

    def commit_registry_intent(
        self, intent: dict[str, Any], *, term: int | None = None
    ) -> bool:
        """Leader-only commit of a validated registry intent."""
        if self.role != RaftNodeState.LEADER:
            logger.warning("[REJECTION] Follower %s cannot commit registry intent.", self.node_id)
            return False

        active_term = self.current_term if term is None else term
        mutation = intent.get("registry", intent)
        if not isinstance(mutation, dict):
            return False
        if not self.append_registry_intent(active_term, mutation):
            return False
        self.commit_index = len(self.registry_log)
        logger.info("[LOG COMMITTED] State mutation index %s secured.", self.commit_index)
        return True

    def replicate_to_followers(self, intent: dict[str, Any]) -> dict[str, bool]:
        """Simulate append-entries RPC fan-out to follower peers."""
        results: dict[str, bool] = {}
        mutation = intent.get("registry", intent)
        for peer in self.peers:
            ok = self.append_registry_intent(self.current_term, mutation)
            results[peer] = ok
        return results

    def tick(self) -> None:
        """Follower watchdog — start election if leader heartbeat expired."""
        if self.role == RaftNodeState.LEADER:
            self._last_heartbeat = time.monotonic()
            return
        if time.monotonic() - self._last_heartbeat > self._election_timeout_s:
            self.initiate_election()

    def latest_committed_mutation(self) -> dict[str, Any] | None:
        if self.commit_index <= 0 or not self.registry_log:
            return None
        return self.registry_log[self.commit_index - 1].get("mutation")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    cluster = HardwareConsensusCluster(node_id="m5_core_01", peers=["m5_core_02", "m5_core_03"])
    cluster.initiate_election()
    cluster.commit_registry_intent({"registry": {"units": {"heartbeat": {"frequency_hz": 2}}}})
