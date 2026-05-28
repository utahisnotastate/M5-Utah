from m5resolver.fluxwire import ContinuousWire, FluxGraph


def test_wire_routes_only_when_value_changes():
    wire = ContinuousWire("accel.x", ("speaker", "tone", "frequency"), lambda x: round(abs(x) * 10, 2))
    mapped, changed = wire.route(1.0)
    assert changed is True
    assert mapped == 10.0

    mapped, changed = wire.route(1.0)
    assert changed is False
    assert mapped is None


def test_fluxgraph_creates_nested_patch():
    graph = FluxGraph()
    graph.add_wire(ContinuousWire("accel.x", ("display", "text", "payload"), lambda x: f"x={x:.2f}"))
    patch = graph.resolve_intent_patch({"accel": {"x": 0.33}})
    assert patch == {"display": {"text": {"payload": "x=0.33"}}}
