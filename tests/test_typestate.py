"""Formal typestate transition contract tests."""

from m5resolver.typestate import SystemTypestateEnforcer


def test_formal_typestate_transition_contracts():
    """
    Asserts that the system typestate engine successfully blocks illegal runtime transitions
    while cleanly processing valid lifecycle milestones.
    """
    enforcer = SystemTypestateEnforcer()

    assert enforcer.verify_transition_legality("IDLE", "BUSY") is True
    assert enforcer.verify_transition_legality("BUSY", "IDLE") is True

    assert enforcer.verify_transition_legality("INITIALIZING", "BUSY") is False
    assert enforcer.verify_transition_legality("SUSPENDED", "INITIALIZING") is False


def test_typestate_blocks_illegal_intent_transition():
    enforcer = SystemTypestateEnforcer()
    intent = {
        "typestate": {"current": "BUSY", "target": "INITIALIZING"},
    }
    errors = enforcer.validate_intent_typestate(intent)
    assert errors
    assert "typestate_violation" in errors[0]
