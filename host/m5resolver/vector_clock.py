from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("m5resolver.vector")


class VectorClockTracker:
    """
    Causal vector ordering for distributed m5-utah mesh nodes.

    Tracks logical clocks per node ID to detect dropped messages and
    out-of-order configuration cascades without wall-clock synchronization.
    """

    def __init__(self, host_id: str) -> None:
        self.host_id = host_id
        self.clock_vector: dict[str, int] = {self.host_id: 0}
        self.causal_violations = 0
        self.last_rejected_sender: str | None = None

    def increment_local_event(self) -> dict[str, int]:
        self.clock_vector[self.host_id] = self.clock_vector.get(self.host_id, 0) + 1
        return self.clock_vector.copy()

    def merge_and_verify_causality(
        self, incoming_vector: dict[str, int], sender_id: str
    ) -> bool:
        self.increment_local_event()

        for node in incoming_vector:
            if node not in self.clock_vector:
                self.clock_vector[node] = 0

        local_sender_clock = self.clock_vector.get(sender_id, 0)
        incoming_sender_clock = int(incoming_vector.get(sender_id, 0))

        if incoming_sender_clock > local_sender_clock + 1:
            self.causal_violations += 1
            self.last_rejected_sender = sender_id
            logger.warning(
                "[CAUSAL DRIFT] Network dropped messages from %s "
                "(expected <= %s, got %s).",
                sender_id,
                local_sender_clock + 1,
                incoming_sender_clock,
            )
            return False

        for node, counter in incoming_vector.items():
            self.clock_vector[node] = max(self.clock_vector[node], int(counter))

        logger.debug("[VECTOR CLOCK SYNCED] Cluster temporal state: %s", self.clock_vector)
        return True

    def stamp_event(self, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        stamped = dict(payload or {})
        stamped["sender_id"] = self.host_id
        stamped["vector_clocks"] = self.increment_local_event()
        return stamped

    @staticmethod
    def happens_before(a: dict[str, int], b: dict[str, int]) -> bool:
        """Return True if vector a strictly precedes b in causal order."""
        all_le = all(a.get(node, 0) <= b.get(node, 0) for node in set(a) | set(b))
        strictly_less = any(a.get(node, 0) < b.get(node, 0) for node in set(a) | set(b))
        return all_le and strictly_less

    def apply_sync_vector(self, sync_vector: dict[str, int]) -> None:
        for node, counter in sync_vector.items():
            self.clock_vector[node] = max(self.clock_vector.get(node, 0), int(counter))
