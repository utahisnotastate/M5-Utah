from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import socket
import threading
from typing import Any, Callable

logger = logging.getLogger("m5resolver.mesh")


class FluxwireGossipMesh:
    """
    UDP gossip mesh for decentralized registry/telemetry verification.
    Nodes share fingerprints and degraded-state alerts without a central broker.
    """

    def __init__(
        self,
        node_id: str,
        port: int = 23023,
        on_peer_degraded: Callable[[dict], None] | None = None,
    ) -> None:
        self.node_id = node_id
        self.port = port
        self.peers: set[str] = set()
        self.known_registry_fingerprints: dict[str, str] = {}
        self._local_fingerprint = ""
        self._local_status = "operational"
        self._on_peer_degraded = on_peer_degraded
        self._socket: socket.socket | None = None
        self._loop: asyncio.AbstractEventLoop | None = None
        self._thread: threading.Thread | None = None
        self._running = False

    def _ensure_socket(self) -> socket.socket:
        if self._socket is not None:
            return self._socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(("", self.port))
        sock.setblocking(False)
        self._socket = sock
        return sock

    @staticmethod
    def fingerprint_registry(registry: dict) -> str:
        payload = json.dumps(registry, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]

    def update_local_registry(self, registry: dict) -> None:
        self._local_fingerprint = self.fingerprint_registry(registry)
        self.known_registry_fingerprints[self.node_id] = self._local_fingerprint

    def update_local_status(self, status: str) -> None:
        self._local_status = status

    def start_background(self) -> None:
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run_loop_thread, daemon=True)
        self._thread.start()
        logger.info("Gossip mesh started on port %s as %s", self.port, self.node_id)

    def stop(self) -> None:
        self._running = False
        if self._loop and self._loop.is_running():
            self._loop.call_soon_threadsafe(self._loop.stop)
        if self._thread:
            self._thread.join(timeout=2.0)
        if self._socket:
            self._socket.close()
            self._socket = None

    def _run_loop_thread(self) -> None:
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        try:
            self._loop.run_until_complete(self.start_mesh_loops())
        finally:
            self._loop.close()

    async def start_mesh_loops(self) -> None:
        await asyncio.gather(self._listen_for_gossip(), self._broadcast_heartbeat())

    async def _broadcast_heartbeat(self) -> None:
        while self._running:
            payload = {
                "sender_id": self.node_id,
                "type": "gossip_heartbeat",
                "version": "0.3.2",
                "fingerprint": self._local_fingerprint,
                "status": self._local_status,
            }
            message = json.dumps(payload).encode("utf-8")
            try:
                self._ensure_socket().sendto(message, ("255.255.255.255", self.port))
            except OSError as exc:
                logger.debug("Broadcast skipped: %s", exc)
            await asyncio.sleep(5)

    async def _listen_for_gossip(self) -> None:
        loop = asyncio.get_event_loop()
        while self._running:
            try:
                data, addr = await loop.run_in_executor(None, self._recv_nonblocking)
            except BlockingIOError:
                await asyncio.sleep(0.05)
                continue
            if not data:
                await asyncio.sleep(0.05)
                continue
            try:
                payload = json.loads(data.decode("utf-8"))
            except json.JSONDecodeError:
                continue

            sender_id = payload.get("sender_id")
            if not sender_id or sender_id == self.node_id:
                continue

            peer_ip = addr[0]
            if peer_ip not in self.peers:
                logger.info("[MESH DISCOVERY] node %s at %s", sender_id, peer_ip)
                self.peers.add(peer_ip)

            fp = payload.get("fingerprint")
            if isinstance(fp, str):
                self.known_registry_fingerprints[sender_id] = fp

            if payload.get("status") == "degraded_state":
                logger.warning("[MESH NOTICE] peer %s degraded; relaying profile", sender_id)
                if self._on_peer_degraded:
                    self._on_peer_degraded(payload)

            if payload.get("type") == "registry_gossip":
                registry = payload.get("registry")
                if isinstance(registry, dict):
                    self.known_registry_fingerprints[sender_id] = self.fingerprint_registry(registry)

    def _recv_nonblocking(self) -> tuple[bytes, tuple[str, int]]:
        try:
            return self._ensure_socket().recvfrom(4096)
        except BlockingIOError:
            raise

    def broadcast_registry_gossip(self, registry: dict) -> None:
        payload = {
            "sender_id": self.node_id,
            "type": "registry_gossip",
            "fingerprint": self.fingerprint_registry(registry),
            "registry": registry,
            "status": self._local_status,
        }
        message = json.dumps(payload).encode("utf-8")
        try:
            self._ensure_socket().sendto(message, ("255.255.255.255", self.port))
        except OSError as exc:
            logger.debug("Registry gossip send failed: %s", exc)
