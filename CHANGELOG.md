# Changelog

## 0.8.2 - 2026-05-29

- **Omega defense stack**: `StochasticShield`, `MeshStateMirror`, `AmnesiaKernel`, `ChronoScheduler`, `TensorVoidLinkage`, `LazarusDaemon` via `OmegaDefense` coordinator
- **Field graph compiler**: `host/utah_flux/field_compiler.py` for sanctum-style `nodes`/`bindings` projects; RGB565 hex color fix
- **UtahClaw launchers**: root `Start UtahClaw Studio.bat`, `Install UtahClaw.bat`, auto-install `host[claw]` deps, visible daemon window on errors
- **Firmware flash helper**: `firmware/flash-cores3.ps1`; CoreS3 upload troubleshooting in `firmware/README.md`
- **Tests**: `tests/test_field_compiler.py`
- **Docs**: bilingual Omega defense + field graph guides; ADR 0045

## 0.8.1 - 2026-05-29

- **Intent-Resolution Canvas**: polished `utah_studio.html` (silicon + UtahClaw panels)
- Windows launchers: `Start UtahClaw Studio.bat`, `Start Omniscient Studio.bat`
- Bilingual docs: UtahClaw, Omniscient, architecture (zh), intent canvas guides

## 0.8.0 - 2026-05-29

- **Immortal Bootloader**: `ImmortalDiscovery` Core 0 I2C autonomic discovery (flash once)
- **Omniscient OS**: `utah-flux-omniscient` FastAPI daemon + WebSocket auto-discovery GUI
- **UtahClaw**: `utah-claw-studio` local Ollama vibe-coding + auto-heal serial loop
- Shared `HardwareMatrix` Espressif USB scan (VID 303A); ADR 0044

## 0.7.0 - 2026-05-29

- **m5-secure**: `SecureWireEncoder` monotonic anti-replay attestation on fast-path frames
- Firmware `SecureWireFence` validates `#A` (`0x23 0x41`) sequences on Core 0 before ring push
- `send_fastpath()` wraps `##` / `#P` frames with secure sequence tokens when enabled
- Competitor comparison matrix in README; architecture security lifecycle docs; ADR 0043

## 0.6.9 - 2026-05-29

- m5-dashboard: `TerminalStateVisualizer` real-time structural state matrix
- `[HEALTH_VITALS_STREAM]:` frames drive live dashboard when `enable_dashboard=True`
- `test_visualizer_data_ingestion_bounds` in validation suite; ADR 0042

## 0.6.8 - 2026-05-29

- m5-typestate: `SystemTypestateEnforcer` formal protocol state validation
- Host `send_intent` preflight blocks illegal typestate transitions
- m5-rollback: `OtaRollbackFence` double-buffered OTA partition swap in integrated boot
- `test_typestate.py` contract assertions; ADR 0041

## 0.6.7 - 2026-05-29

- Unified m5-kernel entry point: `m5IntegratedKernelBoot()` consolidates firmware boot
- Host `INTEGRATED_BOOT_SEQUENCE` / `UNIFIED_LIFECYCLE_STAGES` lifecycle documentation
- Architecture doc unified development lifecycle section with mermaid flow
- `test_m5_unified_lifecycle_boot_sequence`; ADR 0040

## 0.6.6 - 2026-05-29

- m5-pipeline: GitHub Actions `.github/workflows/m5utah-ci.yml`
- Parallel host pytest matrix + PlatformIO firmware compilation jobs
- `platformio.ini` dual targets (CoreS3 + Core ESP32), `-O3`, ArduinoJson 7.x pin
- Firmware header/cast fixes for clean PlatformIO CI builds
- ADR 0039 CI/CD validation pipeline

## 0.6.5 - 2026-05-29

- m5-android-mesh: `AndroidMeshParticipant` gossip → audit → USB binwire routing
- `MeshRegistryMirror`, enhanced `FluxwireMeshNode` with `registry_gossip` handling
- Host `android_mesh.py` preflight audit and gossip binwire compiler
- `test_android_mesh_gossip_preflight_and_binwire`; ADR 0038

## 0.6.4 - 2026-05-29

- Mesh registry synchronizer: host-side 2PC via `MeshStateSynchronizer`
- `transaction_prepare` / `transaction_commit` with `TransactionalCoreManager` heap gates
- `send_cluster_registry_mutation()` and `ControllerClusterTransport` adapter
- Graph validation + optional delta commit compilation in sync mesh
- `test_mesh_two_phase_commit_safety`; ADR 0037

## 0.6.3 - 2026-05-29

- Zero-copy cross-core stream piping: `#S` / `0x23 0x53` fixed stream frames
- `HostStreamPacker.pack_stream_frame()` and `StreamIntentDecoder` on Core 1
- Integrated into existing `CrossCorePipe` ring (Core 0 ingest, no main.cpp task rewrite)
- `send_stream_frame()`, `synchronize_stream_frame()` orchestration hooks
- `test_stream_payload_binary_signature_contracts`; ADR 0036

## 0.6.2 - 2026-05-29

- m5-autofence: closed-loop telemetry remediation (`#R` / `0x23 0x52`)
- `AutonomousRemediationEngine` with `[HEALTH_VITALS_STREAM]:` hex vitals uplink
- Firmware `SystemHealthHarvester` + `RemediationDecoder` on Core 0/1 path
- Controller auto-injects defensive throttles on degraded heap/jitter profiles
- `test_closed_loop_remediation_packing_contracts`; ADR 0035

## 0.6.1 - 2026-05-29

- m5-vectorfence: hot-swappable IRAM interrupt vector patching (`#I` / `0x23 0x49`)
- `HostVectorCompiler.compile_vector_patch()` and `VectorFenceEngine` on Core 1
- Atomic ISR pointer swap with 4-channel virtual gate handles (512-byte cap)
- `send_vector_fence_patch()`, `synchronize_vector_fence()` orchestration hooks
- `test_interrupt_vector_packing_contracts`; ADR 0034

## 0.6.0 - 2026-05-29

- m5-flatten: speculative branch-flattening jump matrix (`#F` / `0x23 0x46`)
- `BranchFlattenCompiler.compile_jump_vector()` and `MicroJumpKernel` on Core 1
- Lockless `BranchStateMirrorEntry` table + 16-slot function-pointer jump matrix
- `send_branch_flatten()`, `synchronize_branch_flatten()` orchestration hooks
- `test_branch_flatten_packing_contracts`; ADR 0033

## 0.5.9 - 2026-05-29

- Complete state synchronization loop: `UnifiedOrchestrationController`
- `synchronize_intent_delta()` — validate → scheduler → `##D` bitmap flush
- `IntentValidator.validate()` bool helper; `IntentController.unified_orchestrator()`
- `test_unified_orchestration_synchronization_lifecycle`; ADR 0032

## 0.5.8 - 2026-05-29

- Bitmapped graph-relational delta overlays: `##D` fixed 10-byte frames (`!HHI`)
- `BitmappedDeltaCompiler.compile_bitmap_delta()` and `IntentController.send_bitmap_delta()`
- Firmware `DeltaEngine::processBitmapDeltaPayload()` on Core 0/1 demux path
- `test_bitmapped_delta_packing_contracts`; ADR 0031

## 0.5.7 - 2026-05-29

- Virtual Event Pipe Grid: `[VIRTUAL_EVENT_STREAM]:` transport on Fluxwire
- `VirtualEventRouter.ingest_mesh_signal()`, `parse_event_line()`, `imu_tilt_event` default route
- Firmware `VirtualEventGrid` with IMU-tuned `StochasticTelemetryFilter` and `broadcastPristineEvent()`
- Core 1 `scanFilteredImuVirtualEvents()` — Kalman-filtered tilt events without recompile
- `test_virtual_event_multiplexing_integrity`; ADR 0030

## 0.5.6 - 2026-05-29

- m5-jit pipeline completion: `M5JitPipeline` with differential registry delta support
- `verify_iram_payload_safe()`, `compile_intent_to_assembly()` alias, `-O3` JIT compile
- `IntentController.compile_and_send_jit_with_delta()` for JIT + 0xDE patch
- Firmware `M5Jit.h` integration header; `test_instruction_ram_allocation_constraints`
- ADR 0029 m5-jit pipeline completion

## 0.5.5 - 2026-05-29

- Dynamic priority dependency resolution (Feature 58): bus + pin + dependency tier propagation
- `SchedulingAudit`, `compile_with_audit()`, `audit_registry_file()` preflight APIs
- Controller logs scheduler audit before intent transmit
- `test_predictive_priority_inheritance_contracts` and registry audit tests
- ADR 0028 dynamic priority dependency resolution

## 0.5.4 - 2026-05-29

- Integrated asymmetric m5-kernel formalized in `M5IntegratedKernel.h`
- RPP micro-execution routes through PriorityGatekeeper on Core 1
- Scheduler compiler self-test harness; integrated kernel contract tests
- ADR 0027 integrated m5-kernel completion documentation

## 0.5.3 - 2026-05-29

- Android Host Integration Layer: `FastPathUsbBridge.kt` USB Host binwire/RPP transport
- `WireFrames.kt` Big-endian packers matching firmware `DirectHardwareCommand`
- `FluxwireMeshNode.kt` UDP gossip mesh peer for companion apps
- Host `android_bridge.py` contract mirror; `test_android_payload_binary_signature`
- Capability `android_usb_host_bridge`; ADR 0026

## 0.5.2 - 2026-05-29

- Asymmetric Remote Procedure Piping (RPP): `#P` fixed-width frames via `HostRPPCompiler`
- Firmware `MicroExecutionKernel` / `RPPDecoder` for stack-local opcode dispatch
- Core 0 CrossCorePipe demux for `0x23 0x50`; `send_rpp()` on host orchestrator
- Intent schema `rpp` block; `rpp_execute` vibe action; alignment contract tests
- Capability `asymmetric_rpp_piping`; ADR 0025

## 0.5.1 - 2026-05-29

- Telemetry-driven self-healing loop (Feature 53): `AutonomousMitigationEngine`
- Firmware `TelemetryHealth` metrics: `task_jitter_ms`, active unit/pin tracking
- `[TELEMETRY_STREAM]:` prefixed diagnostic frames on degraded nodes
- Host auto-injects binwire throttle patches when heap/jitter thresholds breach
- ADR 0024 telemetry self-healing diagnostic loops

## 0.5.0 - 2026-05-29

- Dual-core non-blocking execution harness (Feature 52) formalized in `DualCoreHarness.h`
- Core 0 ingest priority elevated; ring allocation logging with 512-byte minimum contract
- Registry `fast_path_bridge` units with `execution_core_target` and `buffer_allocation_bytes`
- Host `dual_core_harness.py` validation; cross-core schema regression tests
- Capability `dual_core_execution_harness`; ADR 0023

## 0.4.9 - 2026-05-29

- WebUSB vibe gateway server (`vibe_server.py`) with WebSerial IDE on port 8023
- Vibe compile pipeline: schema validation, resource preflight, binwire/JSON wire routing
- GPIO natural-language prompts compile to `fast_track_gpio` binwire frames
- `IntentController.compile_vibe_for_wire()` for host orchestration integration
- Fast-path encoder bounds regression test; vibe server HTTP integration tests
- ADR 0022 WebUSB vibe gateway and compile pipeline

## 0.4.8 - 2026-05-29

- Resource-aware orchestrator (`ResourceOrchestrator`) with pressure-based intent deferral
- M5Kernel integration: orchestration tick, critical-path preservation for registry/binary
- Host `HostResourceOrchestrator` preflight in `IntentController.send_intent()`
- Orchestrator telemetry metrics and `resource_aware_orchestrator` capability
- ADR 0021 resource-aware orchestration; architecture guide updated

## 0.4.7 - 2026-05-29

- Central processing kernel (`M5Kernel`) unifying dual-core protocol and orchestration loops
- Core 0 serial ingest + Core 1 application task replace Arduino `loop()` processing
- Registry intents staged through virtual handles under gatekeeper supervision
- Kernel telemetry metrics and `m5_central_kernel` capability
- Architecture guide at `docs/en/architecture.md`; ADR 0020 m5 central processing kernel

## 0.4.6 - 2026-05-29

- Predictive priority-inheritance gatekeeper (`PriorityGatekeeper`) for shared firmware assets
- I2C/SPI hot-swap wrapped in proactive priority boost + mutex gates
- Host scheduling matrix compiler with pin-contention tier escalation
- `IntentController` auto-applies scheduler compilation before registry deploy
- Registry `realtime_critical` and `assigned_priority_tier` fields with validation
- ADR 0019 priority gatekeeper and scheduler compiler

## 0.4.5 - 2026-05-29

- TDMA shared-bus arbitrator (`BusArbitrator`) with mutex-guarded I2C/SPI hot-swap windows
- Registry `bus_arbitration_window_ms` for per-unit TDMA slot configuration
- Hamming (7,4) telemetry ECC encoder on firmware and repair decoder on host
- `FluxGraph.repair_telemetry()` and automatic ECC repair in `IntentController.read_frame()`
- Bus metrics in telemetry; ADR 0018 TDMA bus arbitrator and telemetry ECC

## 0.4.4 - 2026-05-29

- Virtual handle memory manager (`HandleMemoryManager`) with 32-slot matrix and 2 KB static pool
- Predictive heap compaction on supervisor tick and `memory_compact` intent
- Host asymmetric heap profiler (`HostMemoryProfiler`) with pre-flight registry safety checks
- `IntentController.send_memory_compact()` and auto-compaction before blocked pushes
- Registry `allocation_handle_id` and `buffer_size_bytes` fields with validation
- Telemetry handle pool metrics; ADR 0017 virtual handle memory and heap compaction

## 0.4.3 - 2026-05-29

- Cross-core lock-free ring pipe (`CrossCorePipe`) with Core 0 serial ingest and Core 1 drain
- In-place zero-copy tokenizer for non-JSON declarative payloads (`InPlaceTokenizer`)
- Host stream relay encoder and fluxwire ring-frame alignment validation
- `IntentController.send_relay_intent()` with pre-flight frame boundary checks
- I2C/SPI bus `frequency_hz` safety validation distinct from unit loop frequency cap
- ADR 0016 cross-core ring pipe and zero-copy tokenizer

## 0.4.2 - 2026-05-29

- In-memory assembly trampoline hooks (`AssemblyHook`) with IRAM fence validation on firmware
- Differential memory overlay compiler (`HardwareMemoryCompiler`) and `#M` wire frames
- `IntentController.send_memory_overlay()` and `DriverRegistry.compile_overlay_for_unit()`
- Unified binary demux for overlay (`#M`), binwire (`##`), and delta (`0xDE 0xDA`) frames
- Address boundary fence tests and `tests/test_memory_compiler.py`
- ADR 0015 assembly trampolines and memory overlays

## 0.4.1 - 2026-05-29

- DAG state graph engine (`StateGraphEngine`) for dependency-aware registry mutations
- Bitmapped delta compression (`DeltaEncoder` / `DeltaEngine`) with 16-slot bitmask wire format
- `DriverRegistry` topological validation and minimal cascade patches
- `IntentController.send_graph_registry_delta()` for compact mesh updates
- Registry `depends_on` and `slot_id` schema fields
- ADR 0014 DAG state graph and delta compression

## 0.4.0 - 2026-05-29

- Resource-aware intent pruning (`HardwareCostModel`) with 40% heap headroom gate
- Auto-prune in `IntentController.send_intent()` using live telemetry free heap
- Speculative shadow staging buffer for fail-safe task promotion on firmware
- Stable snapshot revert when speculative fork validation fails
- Capabilities: `resource_pruning`, `speculative_staging`
- ADR 0013 resource pruning and speculative staging

## 0.3.9 - 2026-05-29

- Vector clock causal synchronization (`VectorClockTracker` / m5-vectorwire)
- Firmware `VectorTelemetryBuilder` embeds logical clocks in telemetry and events
- FluxGraph causal gating suppresses out-of-order intent patches
- `vector_clock_sync` host→device clock mirror intents
- Telemetry schema updated with `vector_clocks` and `sender_id`
- ADR 0012 vectorwire causal sync

## 0.3.8 - 2026-05-29

- Runtime JIT hot-loader (`RuntimeLinker`) with IRAM executable memory allocation
- Host JIT compiler pipeline (`HostJitCompiler`) for Xtensa `.text` extraction
- `native_jit` intent channel with hex payload validation (4096-byte IRAM cap)
- `IntentController.compile_and_send_jit()` for compile → sign → inject workflow
- JIT validation tests and schema updates
- ADR 0011 runtime JIT hot-loading

## 0.3.7 - 2026-05-29

- Zero-trust cryptographic enclave (`CryptoEnclave`) with SHA-256 intent verification on device
- Kalman telemetry filtering for IMU axes (`TelemetryKalmanFilter` / `TelemetryFilterBank`)
- Host intent signing and verification (`security.py`, `sha256-canonical-v1`)
- CLI `--sign` and `--require-registry-signature` flags
- Security alarm frames and validation tests in `tests/test_validation.py`
- ADR 0010 crypto enclave and Kalman filter

## 0.3.6 - 2026-05-29

- Raft-based hardware consensus cluster (`HardwareConsensusCluster` / m5-raft)
- FluxGraph leader-gated registry commits with mesh gossip propagation
- FreeRTOS sandbox isolation with static stacks and stable snapshot revert
- `IntentController` optional `enable_consensus` for clustered deployments
- Regression tests for election lifecycles and leader authorization
- ADR 0009 raft consensus and sandboxing

## 0.3.5 - 2026-05-29

- Binary fast-path intent serialization (`BinwireEncoder` / m5-binwire)
- Firmware zero-copy decoder (`BinwireDecoder`) bypasses JSON on `##` magic frames
- CLI `--fastpath` flag validates JSON then sends 10-byte binary frames
- `IntentController.send_fastpath()` for RPP-style wire transport
- Integration tests in `tests/test_binwire.py`
- ADR 0008 binwire fast-path serialization

## 0.3.4 - 2026-05-29

- Zero-downtime state forking (`StateForker`) replaces aggressive task teardown on registry hot-reload
- Virtual event router (`VirtualEventRouter`) decouples hardware signals from intent callbacks
- Firmware emits `hardware_event` frames (button press, motion spike) over Fluxwire
- `refresh_sequence_id` on registry units for deterministic shadow swap ordering
- `make verification` alias for lint + typecheck + pytest gate
- ADR 0007 zero-downtime fork and event piping

## 0.3.3 - 2026-05-28

- Time-travel state journal in firmware (`TimeTravelJournal`)
- Host replay engine (`HostReplayEngine`) with automatic controller interception
- `schemas/time_travel.schema.json` contract
- CI schema-check workflow runs full pytest suite
- Utah Flux Live Log displays time-travel dumps
- ADR 0006 time-travel replay

## 0.3.2 - 2026-05-28

- Dynamic bus multiplexing firmware (`DynamicMultiplexer`) for runtime I2C/SPI/PWM/GPIO
- UDP gossip mesh (`FluxwireGossipMesh`) for decentralized registry/telemetry verification
- Bus topology validation and `IntentValidator` strict gate
- Utah Flux **Attach I2C Sensor** brick
- ADR 0005 dynamic bus and gossip mesh

## 0.3.1 - 2026-05-28

- Full documentation refresh for Utah Flux Studio (EN + 中文)
- Per-audience tutorials (children, non-technical, technical, engineers, employees)
- Updated MkDocs navigation, compatibility matrix, operations runbooks

## 0.3.0 - 2026-05-28

- Utah-Flux visual library (`host/utah_flux/`) with Lego brick catalog and compiler
- Utah Flux Studio GUI — drag-and-drop IDE, no CLI required for users
- Double-click launchers (`Start Utah Flux Studio.bat`)
- Starter templates, save/open `.flux.json` projects
- WebSerial Play/Stop from the browser

## 0.2.0 - 2026-05-28

- Vibe-IDE browser gateway (`m5vibe`) with WebSerial frontend
- Agentic controller with closed-loop remediation and device state memory
- Simulation-in-the-loop and safety gate validation
- Hardware Context Protocol schemas and bounty-enabled registry
- Firmware registry hot-reload with semantic actions and RTOS unit supervisor

## 0.1.0 - 2026-05-28

Initial consolidated release:

- Universal firmware intent terminal with telemetry + ACK protocol
- Host runtime package (`m5resolver`) with controller, FluxWire, and registry loader
- Dynamic unit registry (`registry/units.json`)
- End-to-end sample (`examples/tilt_tone.py`)
- Bilingual audience documentation and migration playbook
- Tests, CI workflow, and contributor/community governance files
