from m5resolver.consensus import HardwareConsensusCluster, RaftNodeState


def test_append_registry_intent_rejects_stale_term():
    node = HardwareConsensusCluster("n1", ["n2"])
    node.current_term = 5
    assert node.append_registry_intent(4, {"units": {}}) is False


def test_leader_commits_and_replicates_log():
    node = HardwareConsensusCluster("n1", ["n2", "n3"])
    node.initiate_election()
    intent = {"registry": {"units": {"sensor": {"frequency_hz": 4}}}}
    assert node.commit_registry_intent(intent) is True
    assert len(node.registry_log) == 1
    assert node.latest_committed_mutation() == intent["registry"]


def test_follower_cannot_commit():
    node = HardwareConsensusCluster("n2", ["n1"])
    assert node.role == RaftNodeState.FOLLOWER
    assert node.commit_registry_intent({"registry": {"units": {}}}) is False
