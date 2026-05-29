# M5Stack Employee Migration Playbook

## Executive summary

Utah Flux Studio is the **default customer-facing product**. Legacy per-module repositories should move to reference/bridge/retire states for new development.

## Employee tutorial

Step-by-step first month: [Employee Tutorial](tutorials/employee-tutorial.md).

## Why migrate

| Metric | Legacy | Utah Flux |
|--------|--------|-----------|
| Time to first demo | Hours (toolchain) | Minutes (starter + Play) |
| Classroom support load | High (compile errors) | Low (visual projects) |
| Transparency | Hidden in C++ | `.flux.json` + registry |

## 30-60-90 plan

### Days 0–30

- Freeze net-new APIs in fragmented repos
- Publish Utah Flux quickstart in EN/ZH
- Flash unified firmware on demo hardware

### Days 31–60

- Port top 20 workflows to `.flux.json` templates
- Registry entries for active Units
- Support trained on GUI-only path

### Days 61–90

- Enforce “new features in Utah Flux / registry only”
- Publish KPI dashboard
- Announce legacy repo sunset dates

## Repository states

1. **Core** — this repo (`M5-Utah`)
2. **Bridge** — thin adapters during transition
3. **Reference** — read-only examples
4. **Retire** — no new features

## Role expectations

- **Firmware:** thin runtime, semantic actions
- **DevRel:** Utah Flux demos, not PlatformIO-first
- **Support:** request `.flux.json`, check Live Log
- **PM:** roadmap in bricks/templates/registry, not repo count

## KPIs

- % new features via Utah Flux
- Support tickets “which library?”
- Time to first Play in workshops
