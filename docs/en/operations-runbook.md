# Operations Runbook

## Health checks

1. Confirm serial port visibility
2. Confirm telemetry cadence
3. Send smoke-test intent and verify ACK
4. Verify battery/charging values are sane

## Incident flow

1. Capture serial logs
2. Record firmware commit and host version
3. Reproduce with minimal intent
4. Isolate transport vs parsing vs logic failure
5. File issue with logs and reproduction steps
