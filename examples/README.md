# Examples

## `tilt_tone.py`

Maps accelerometer X-axis telemetry to:

- display text update
- speaker tone frequency

Run:

```bash
python examples/tilt_tone.py --port COM3
```

Use this as a template for additional intent-driven applications.

## `agent_loop.py`

Runs closed-loop agentic control with telemetry observation and corrective intents.

```bash
python examples/agent_loop.py --port COM3
```

## `sample-intent.json`

Ready-to-send sample intent payload for CLI validation and smoke tests:

```bash
m5resolver --port COM3 --intent-file examples/sample-intent.json --dry-run
```
