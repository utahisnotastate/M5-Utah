# Operations Runbook

## UtahClaw Omniscient Studio health checks

1. Run `Install UtahClaw.bat` once (installs `host[claw]`: FastAPI, Uvicorn, Ollama client).
2. `ollama run llama3` running locally.
3. Double-click `Start UtahClaw Studio.bat` — browser opens `http://127.0.0.1:8024`.
4. **UtahClaw Daemon** console window stays open (do not close — server runs there).
5. Status chip shows **NEURAL LINK STABLE** (or agent panel connected).
6. Plug CoreS3 USB — agent panel shows `Linked: COMx` (close Ghost Forge / serial monitor first).
7. Attach ENV III on Grove A — hardware deck shows auto-detected unit.
8. Type intent → **MANIFEST** — agent panel shows deployed JSON/code.

### UtahClaw incidents

| Issue | Action |
|-------|--------|
| `ERR_CONNECTION_REFUSED` | Daemon crashed — read UtahClaw Daemon window; re-run `Install UtahClaw.bat` |
| `fastapi` / `uvicorn` missing | `pip install -e "./host[claw]"` from repo root |
| Port conflict on COM | Only one app (UtahClaw, Ghost Forge, PlatformIO monitor) per port |

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
3. Note firmware version (git commit) and `host` package version (`0.8.2`)
4. Reproduce with same starter template
5. File issue with logs + project file

## Safe recovery

- User clicks **Stop** in Studio
- Agent may push safe-mode intent on low heap (developer builds)
- Re-flash firmware only if runtime corrupted

## No-CLI policy for end users

Support should guide users to GUI steps only. Developers use `examples/agent_loop.py` when needed.
