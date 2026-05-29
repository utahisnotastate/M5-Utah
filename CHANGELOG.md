# Changelog

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
