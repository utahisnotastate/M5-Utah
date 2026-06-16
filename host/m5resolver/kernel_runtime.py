from __future__ import annotations

"""Host-side constants mirroring the firmware m5-kernel dual-core layout."""

M5_KERNEL_CORE_PROTOCOL = 0
M5_KERNEL_CORE_APPLICATION = 1

M5_KERNEL_CAPABILITY = "m5_central_kernel"

DUAL_CORE_CAPABILITY = "dual_core_execution_harness"
TELEMETRY_SELF_HEALING_CAPABILITY = "telemetry_self_healing_loop"
RPP_CAPABILITY = "asymmetric_rpp_piping"
ANDROID_USB_BRIDGE_CAPABILITY = "android_usb_host_bridge"
FAST_PATH_QUEUE_MIN_BYTES = 512
CROSS_CORE_RING_BYTES = 8192

KERNEL_TELEMETRY_METRICS = (
    "kernel_processed_frames",
    "kernel_orchestration_ticks",
    "orchestrator_pressure_level",
    "orchestrator_deferred_frames",
    "gatekeeper_boost_count",
    "gatekeeper_lock_count",
)

GATEKEEPER_CAPABILITY = "priority_inheritance_gatekeeper"
SCHEDULER_COMPILER_CAPABILITY = "host_scheduler_compiler"
TYPESTATE_ENFORCEMENT_CAPABILITY = "formal_typestate_enforcement"
OTA_ROLLBACK_FENCE_CAPABILITY = "ota_rollback_fence"
TERMINAL_DASHBOARD_CAPABILITY = "terminal_state_dashboard"
SECURE_WIRE_CAPABILITY = "secure_wire_anti_replay_fence"
IMMORTAL_DISCOVERY_CAPABILITY = "immortal_i2c_autonomic_discovery"

ORCHESTRATOR_CAPABILITY = "resource_aware_orchestrator"

INTEGRATED_KERNEL_MODULES = (
    "CrossCorePipe",
    "M5Kernel",
    "PriorityGatekeeper",
    "BusArbitrator",
    "HandleMemory",
    "ResourceOrchestrator",
)

ARCHITECTURE_DOC_SECTIONS = (
    "m5-kernel",
    "dual-core",
    "ResourceOrchestrator",
    "CrossCorePipe",
    "HandleMemory",
    "PriorityGatekeeper",
    "BusArbitrator",
    "Integrated Asymmetric",
    "Unified development lifecycle",
)

# Ordered boot stages mirrored by m5IntegratedKernelBoot() in firmware.
INTEGRATED_BOOT_SEQUENCE = (
    "registryRuntimeInit",
    "otaRollbackFenceInit",
    "HandleMemory.initializeMemoryPool",
    "BusArbitrator.initializeArbitrator",
    "PriorityGatekeeper.initializeGatekeeper",
    "jumpKernelInitDefaults",
    "vectorFenceInit",
    "systemHealthHarvesterInit",
    "immortalDiscoveryInit",
    "M5Kernel.start",
    "protocolCoreIngestTask",
    "m5KernelApplicationCoreTask",
)

UNIFIED_LIFECYCLE_STAGES = (
    "compile",
    "validate",
    "transmit",
    "ingest",
    "orchestrate",
    "observe",
)
