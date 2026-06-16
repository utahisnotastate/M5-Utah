# Operations Runbook

## UtahClaw Omniscient Studio health checks

1. `ollama run llama3` running locally
2. Double-click `launch/Start UtahClaw Studio.bat` — browser opens `http://127.0.0.1:8024`
3. Status chip shows **NEURAL LINK STABLE**
4. Plug CoreS3 USB — agent panel shows `Linked: COMx`
5. Attach ENV III on Grove A — hardware deck shows auto-detected unit
6. Type intent → **MANIFEST** — agent panel shows deployed JSON/code

## Omniscient discovery deck

1. `pip install -e "host[daemon]"`
2. `launch/Start Omniscient Studio.bat` → `http://127.0.0.1:8000`
3. Discovery cards appear when I2C devices respond on Port A

## Utah Flux Studio health checks

1. Double-click `Start Utah Flux Studio.bat` — browser opens `http://127.0.0.1:8765`
2. `GET /api/health` returns `{"ok": true}`
3. Load Hello starter → compile chip shows **Ready to play**
4. Connect device → status chip **Connected**
5. Play → telemetry lines appear in Live Log

## Device health checks

1. Serial port visible (Device Manager / `ls /dev/tty*`)
2. Telemetry JSON every ~50 ms
3. ACK after intent: `{"type":"ack","ok":true}`
4. Battery field sane on Core devices

## Incident response

1. Export Live Log text from browser
2. Save customer `.flux.json`
3. Note firmware version (git commit) and `host` package version (`0.3.0`)
4. Reproduce with same starter template
5. File issue with logs + project file

## Safe recovery

- User clicks **Stop** in Studio
- Agent may push safe-mode intent on low heap (developer builds)
- Re-flash firmware only if runtime corrupted

## No-CLI policy for end users

Support should guide users to GUI steps only. Developers use `examples/agent_loop.py` when needed.
