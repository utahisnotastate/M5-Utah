import json

from m5resolver.mesh import FluxwireGossipMesh


def test_registry_fingerprint_stable():
    mesh = FluxwireGossipMesh(node_id="test_node", port=0)
    reg = {"version": 1, "units": [{"unit_id": "a", "bus": "i2c"}]}
    fp1 = mesh.fingerprint_registry(reg)
    fp2 = mesh.fingerprint_registry(reg)
    assert fp1 == fp2
    assert len(fp1) == 16


def test_update_local_registry():
    mesh = FluxwireGossipMesh(node_id="n1", port=0)
    mesh.update_local_registry({"units": {}})
    assert mesh._local_fingerprint
    assert mesh.node_id in mesh.known_registry_fingerprints
