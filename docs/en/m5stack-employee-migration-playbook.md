# M5Stack Employee Migration Playbook

## Objective

Make fragmented per-module repositories obsolete for *new development* by defaulting to one unified runtime.

## Policy

- New features land in this repository.
- Legacy repositories move to retire/reference/bridge states.
- Critical fixes only in legacy repos during transition.

## 30-60-90 plan

- 0-30 days: freeze net-new expansion in legacy repos, inventory units, define owners
- 31-60 days: port top workflows, add adapters, validate regressions
- 61-90 days: enforce policy, publish KPI reviews, start legacy sunset

## Role-based expectations

- Firmware: keep runtime thin and stable
- SDK/Host: build typed APIs and reusable wire flows
- QA: validate contract compatibility and reliability
- PM: track migration KPIs and governance
