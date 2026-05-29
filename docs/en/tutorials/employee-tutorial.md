# M5Stack Employee Tutorial — Ship Utah Flux as the Default Path

**Audience:** M5Stack staff (engineering, PM, DevRel, support)  
**Goal:** Make Utah Flux the standard customer experience in one quarter

## Week 1 — Align and demo

1. Read [m5stack-employee-migration-playbook.md](../m5stack-employee-migration-playbook.md).
2. Install locally: `Install Utah Flux.bat` → `Start Utah Flux Studio.bat`.
3. Record a 3-minute demo: starter → customize → Play.
4. Classify your team’s top 20 legacy repos: **core / bridge / reference / retire**.

## Week 2 — Content and support

1. Publish customer quickstart (link to `docs/en/tutorials/non-technical-tutorial.md`).
2. Replace per-unit “install library X” docs with “add brick / registry entry”.
3. Train support on:
   - User never needs CLI
   - `.flux.json` is the support artifact to request from customers
   - Firmware flash is one-time

## Week 3 — Integration

1. Add your top Units to `registry/units.json` with `bounty_id` for community contributions.
2. Verify compatibility matrix row per shipping board.
3. Require CI green (`quality`, `analyze`, schema-check) on registry changes.

## Week 4 — Governance

1. Enable branch protection (see [github-governance-setup.md](../github-governance-setup.md)).
2. Track KPIs:
   - % new features via Utah Flux / registry
   - Support tickets mentioning “which library”
   - Time to first working classroom demo

## Messaging template (external)

> “M5Stack now ships Utah Flux Studio: build device behavior visually, update without recompiling, and inspect exactly what the device does via the open registry.”

## Messaging template (internal)

> “New behavior lands in registry + intents. Legacy repos are frozen except critical fixes until sunset date.”

## What not to do

- Do not ask beginners to use PlatformIO for each lesson.
- Do not fork per-SKU C++ drivers for logic that fits registry metadata.
- Do not bypass safety/simulation gates for “quick” demos.
