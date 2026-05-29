from pathlib import Path

from m5resolver.kernel_runtime import (
    ARCHITECTURE_DOC_SECTIONS,
    KERNEL_TELEMETRY_METRICS,
    M5_KERNEL_CAPABILITY,
    M5_KERNEL_CORE_APPLICATION,
    M5_KERNEL_CORE_PROTOCOL,
)


def test_kernel_core_constants():
    assert M5_KERNEL_CORE_PROTOCOL == 0
    assert M5_KERNEL_CORE_APPLICATION == 1
    assert M5_KERNEL_CAPABILITY == "m5_central_kernel"


def test_orchestrator_capability_constant():
    from m5resolver.kernel_runtime import ORCHESTRATOR_CAPABILITY

    assert ORCHESTRATOR_CAPABILITY == "resource_aware_orchestrator"


def test_kernel_telemetry_metric_names():
    assert "kernel_processed_frames" in KERNEL_TELEMETRY_METRICS
    assert "kernel_orchestration_ticks" in KERNEL_TELEMETRY_METRICS


def test_architecture_documentation_covers_kernel_layers():
    doc_path = Path(__file__).resolve().parents[1] / "docs" / "en" / "architecture.md"
    assert doc_path.is_file()
    content = doc_path.read_text(encoding="utf-8").lower()
    for section in ARCHITECTURE_DOC_SECTIONS:
        assert section.lower() in content
