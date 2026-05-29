from m5resolver.vector_clock import VectorClockTracker


def test_happens_before_partial_order():
    a = {"node_a": 1, "node_b": 0}
    b = {"node_a": 2, "node_b": 0}
    assert VectorClockTracker.happens_before(a, b) is True
    assert VectorClockTracker.happens_before(b, a) is False


def test_stamp_event_includes_sender_and_clocks():
    tracker = VectorClockTracker("android_host_node")
    stamped = tracker.stamp_event({"type": "intent"})
    assert stamped["sender_id"] == "android_host_node"
    assert stamped["vector_clocks"]["android_host_node"] == 1
