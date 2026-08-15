# ADR-023 — Current Portal is a single-owner Developer Quant Platform

Status: `accepted`  
Accepted by owner: `2026-08-15`  
Issue: `#1555`  
Base at decision: `develop@9dd5887e301ddfeec6df6a3b3e2da24a9ced850f`

## Decision

The **entire current Portal** is a private, single-owner developer/quant/research platform operating on real public market data, simulation, datasets, experiments and local model development.

It is not currently a multi-tenant production trading control plane and is not organized around capital-authority modes.

Current Portal product vocabulary is:

```text
data_source:      REALTIME_PUBLIC | REPLAY
runtime_location: LOCAL | SYNOLOGY
simulation:       integrated product capability
model_state:      BASELINE | CHALLENGER | ACTIVE | ARCHIVED
```

`SHADOW`, `PAPER` and `LIVE` are no longer current Portal product modes. Historical evidence and compatibility fields may retain those labels during migration, but new Portal architecture, UI, API, runtime and acceptance work must not use them as authority states.

Real-money exchange execution is out of current product scope. If ever requested, private trading credentials, capital authority and real order submission require a separate future **Execution/Capital Gateway** architecture/programme rather than shaping the developer Portal today.

## Whole-Portal application

ADR-023 applies to current Portal work across:

- Portal UX/web/BFF/API/control plane;
- WickHunter integration;
- Liquid20 and market-data consumption;
- bot/runtime lifecycle;
- simulation and hypothetical positions/outcomes;
- datasets, labels and research evidence;
- local training, challengers, model comparison and manual active-model selection;
- Portal telemetry/logging/observability;
- persistence and restart recovery;
- Synology deployment/operations;
- Portal CI/E2E/acceptance.

Submodules may not independently reintroduce the superseded mode model.

## Product completion rule

Current Portal work is prioritized by usable owner workflow, not by enterprise trading ceremony.

The canonical vertical slice is:

```text
REALTIME_PUBLIC data
 -> bot/model decisions including NO_TRADE
 -> simulated positions/outcomes
 -> durable chronological dataset/labels
 -> local challenger training
 -> active/challenger/baseline comparison
 -> deliberate active-model selection
 -> restart-safe continued observation in the real Portal
```

A capability is not complete merely because an isolated producer, evidence bundle, protected workflow or exact-SHA proof exists; the applicable owner-facing workflow must actually work.

## Proportionate safety

Keep controls that address present developer-platform risks:

- owner authentication;
- no committed/browser-visible secrets;
- no unnecessary privileged containers or Docker socket exposure;
- server-side validation;
- durable/recoverable state;
- versioned model/config/dataset identities;
- no-lookahead and research-provenance rules;
- training separate from active-model selection;
- bounded external I/O and truthful health/errors;
- ordinary dependency/security CI and restart tests.

Production-grade host certification, protected-target ceremony or capital-execution controls are not universal current Portal gates unless a concrete current risk requires them.

## Supersession matrix

This is a scoped supersession for the **current Portal product**. Historical evidence remains immutable.

| Prior decision | ADR-023 effect for current Portal |
|---|---|
| ADR-003 tenant boundary from day one | **Superseded as current requirement.** Current product is single-owner. Existing tenant fields may remain for compatibility; multi-tenancy is deferred. |
| ADR-004 one bot -> one isolated Freqtrade runtime | **Simplified.** Isolation may be used when useful, but one isolated Freqtrade runtime per bot is not a universal product requirement. |
| ADR-005 deterministic risk before execution | **Narrowed.** Deterministic risk remains useful for simulation/research controls; there is no current real-capital execution authority to gate. |
| ADR-006 immutable identities | **Retained**, interpreted for reproducibility of developer runs, models, datasets/configs and simulated outcomes. |
| ADR-007 training separate from promotion | **Retained**, simplified to challenger creation vs deliberate ACTIVE selection. |
| ADR-008 Decision Black Box | **Retained**; NO_TRADE and later outcomes are first-class research evidence. |
| ADR-009 event/outbox architecture | **Optional implementation choice.** Use only where it reduces current complexity; durable state remains required where authoritative. |
| ADR-010 PostgreSQL/object storage | **Retained as preferred storage direction**, not an enterprise topology gate. |
| ADR-011 Cloudflare ingress | **Retained as convenient private ingress** where used; no production-trading meaning follows. |
| ADR-013 simulator required for full E2E | **Superseded as universal rule.** Deterministic tests remain useful, but real developer E2E on safe public data/simulation is the completion proof for user workflows. |
| ADR-014 production-like E2E | **Superseded as universal current gate.** External protected-route E2E is required only where the changed capability depends on that boundary. |
| ADR-016 PI package decomposition | **Superseded as mandatory decomposition.** Reuse useful components; prefer the smallest complete workflow over package ceremony. |
| ADR-017 Liquid20 read-only/no downstream signal authority | **Superseded for developer workflow.** Liquid20 may feed WickHunter, features, decisions, simulation, datasets and training while remaining public-data-only. |
| ADR-018 quant.molehill.cloud production hostname | **Retained hostname, reinterpreted.** It is the persistent developer Portal endpoint, not proof of a production trading system. |
| ADR-019 architecture registry/evidence authority | **Retained.** ADR-023 and the registry explicitly record this supersession. |
| ADR-020 RuntimeGeneration/Supervisor/Gateway architecture | **No longer the universal current Portal baseline.** Existing code may be reused where valuable; production-grade isolation/reconciliation requirements are not blockers for ordinary developer simulation/research functionality. |
| ADR-021 environment/mode/release dimensions | **Bot-mode portion superseded.** Repository branch/release decisions may remain independently applicable; current Portal uses runtime location and data-source concepts instead of SHADOW/PAPER/LIVE. |
| ADR-022 PAPER-first authority | **Superseded for the entire current Portal.** There are no current Portal SHADOW/PAPER/LIVE product modes. |

## Migration impact

1. Merge ADR-023, `DEVELOPER_QUANT_PORTAL_ARCHITECTURE.md`, registry update and task record.
2. Freeze new mode-driven/production-trading Portal architecture work until exact live-state backlog reclassification is complete.
3. Reclassify open Portal/WickHunter work as `KEEP_NOW | SIMPLIFY | DEFER | OBSOLETE`.
4. Preserve useful existing code; remove or compatibility-wrap only the assumptions that conflict with the new product model.
5. Prioritize one complete developer workflow from realtime public data through observation/simulation, dataset growth, local challenger training and Portal comparison.
6. Simplify CI/deployment/acceptance to risks of the private developer system.
7. Treat a future real-money execution system as a separate architecture programme if the owner ever requests it.

## Current-state truth

ADR-023 changes architecture authority and target migration direction. It does **not** claim current code has already removed SHADOW/PAPER/LIVE literals, tenant fields, RuntimeGeneration, Supervisor/Gateway components, old deployment workflows or historical acceptance evidence.

Exact code/PR/runtime state must be re-inspected before each migration task.

## Detailed architecture

`docs/ai_platform/portal/DEVELOPER_QUANT_PORTAL_ARCHITECTURE.md` is the binding detailed current-Portal architecture for ADR-023.
