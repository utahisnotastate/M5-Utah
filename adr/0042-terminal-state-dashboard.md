# ADR 0042: Real-Time Structural State Visualizer

## Status

Accepted — 2026-05-29

## Context

The m5-utah backend provides dual-core execution, typestate enforcement, and
closed-loop remediation, but developers still had to parse raw serial lines to
understand core allocation, heap headroom, and bus lock state during vibe-coding.

## Decision

### Host — Terminal Dashboard

- `host/m5resolver/dashboard.py` — `TerminalStateVisualizer` renders a
  terminal ASCII matrix from normalized telemetry snapshots
- `normalize_snapshot()` interpolates missing metrics with safe fallbacks
- `IntentController` accepts `enable_dashboard=False` (default); when enabled,
  `[HEALTH_VITALS_STREAM]:` frames invoke `render_system_matrix()` in
  `_process_health_vitals()`
- Outbound intents with validated `typestate.target` update dashboard typestate

### Tests

- `test_visualizer_data_ingestion_bounds` in `tests/test_validation.py`

## Consequences

- Dashboard is opt-in to avoid clearing terminals during headless CI
- Health vitals remediation path unchanged when dashboard is disabled
- Web UI visualizer deferred; terminal matrix satisfies host-plane contract
