import pytest

from m5resolver.resource_orchestrator import (
    CRITICAL_HEAP_THRESHOLD,
    ELEVATED_HEAP_THRESHOLD,
    HostResourceOrchestrator,
    ResourcePressureLevel,
)


def test_evaluate_telemetry_critical_heap():
    orchestrator = HostResourceOrchestrator()
    level = orchestrator.evaluate_telemetry({"metrics": {"free_heap": CRITICAL_HEAP_THRESHOLD - 1}})
    assert level == ResourcePressureLevel.CRITICAL


def test_evaluate_telemetry_elevated_heap():
    orchestrator = HostResourceOrchestrator()
    level = orchestrator.evaluate_telemetry(
        {"metrics": {"free_heap": ELEVATED_HEAP_THRESHOLD - 1}}
    )
    assert level == ResourcePressureLevel.ELEVATED


def test_defer_non_critical_intent_under_critical_pressure():
    orchestrator = HostResourceOrchestrator()
    orchestrator.evaluate_telemetry({"metrics": {"free_heap": 10000}})
    assert orchestrator.should_defer_intent({"display": {"clear": True}}) is True


def test_registry_intent_not_deferred_under_critical_pressure():
    orchestrator = HostResourceOrchestrator()
    orchestrator.evaluate_telemetry({"metrics": {"free_heap": 10000}})
    assert orchestrator.should_defer_intent({"registry": {"units": {}}}) is False


def test_preflight_transmit_returns_errors_when_deferred():
    orchestrator = HostResourceOrchestrator()
    errors = orchestrator.preflight_transmit(
        {"speaker": {"tone": {"frequency": 440, "duration": 50}}},
        free_heap=10000,
    )
    assert errors
    assert orchestrator.deferred_transmit_count == 1


def test_uses_firmware_orchestrator_pressure_level_when_present():
    orchestrator = HostResourceOrchestrator()
    level = orchestrator.evaluate_telemetry(
        {"metrics": {"free_heap": 50000, "orchestrator_pressure_level": 2}}
    )
    assert level == ResourcePressureLevel.CRITICAL


def test_threshold_constants():
    assert ELEVATED_HEAP_THRESHOLD > CRITICAL_HEAP_THRESHOLD
