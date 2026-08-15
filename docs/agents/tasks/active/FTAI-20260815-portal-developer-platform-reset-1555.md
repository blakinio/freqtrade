---
task_id: FTAI-20260815-portal-developer-platform-reset-1555
status: active
repository: blakinio/freqtrade
lane: freqtrade-portal
related_issue: 1555
branch: docs/portal-developer-platform-reset-20260815
base_head: 9dd5887e301ddfeec6df6a3b3e2da24a9ced850f
owner: chatgpt
task_kind: architecture
phase: architecture_reset
prompting_standard_version: 2.1
execution_policy_version: 2
context_pressure: medium
decomposition_decision: single
execution_mode: chat
run_scope: single_task
continuation_policy: stop_at_task_boundary
task_completion_policy: checkpoint_only
user_communication: low_noise
feature_scope:
  type: infrastructure
  user_facing: false
  backend_required: false
  frontend_required: false
  integration_required: false
  e2e_required: false
  completion_claim: internal_only
next_action: Update the accepted decision log and architecture registry with ADR-023, validate document consistency, then open one architecture PR to develop.
---

# Portal developer-platform architecture reset

## Objective

Persist the owner's 2026-08-15 decision that the **entire current Portal** is a private single-owner developer/quant/research platform operating on real public market data, simulation and local model development, rather than a production trading control plane organized around SHADOW/PAPER/LIVE.

## Scope

Owned paths:

- `docs/ai_platform/portal/DEVELOPER_QUANT_PORTAL_ARCHITECTURE.md`
- `docs/ai_platform/portal/ARCHITECTURE_DECISIONS.md`
- `ARCHITECTURE_REGISTRY.yaml`
- this task record

No product/runtime code mutation is part of this task.

## Acceptance

- [ ] ADR-023 is recorded as owner-accepted and explicitly applies to the whole current Portal.
- [ ] Conflicting current-Portal assumptions in ADR-003/004/005/013/014/016/017/020/021/022 are explicitly scoped/superseded without rewriting historical evidence.
- [ ] The canonical developer Portal vocabulary is durable: `REALTIME_PUBLIC | REPLAY`, `LOCAL | SYNOLOGY`, integrated simulation, `BASELINE | CHALLENGER | ACTIVE | ARCHIVED`.
- [ ] Real-money exchange execution is out of current product scope and requires a separate future Execution/Capital Gateway decision if ever desired.
- [ ] `ARCHITECTURE_REGISTRY.yaml` names ADR-023 as the latest current Portal product overlay and marks old PAPER-first/mode architecture as superseded for current Portal scope.
- [ ] Backlog migration requires `KEEP_NOW | SIMPLIFY | DEFER | OBSOLETE` reclassification from exact live state before code removal.
- [ ] Documentation does not claim code migration complete.
- [ ] YAML syntax and document consistency are validated.
- [ ] One PR targets `develop`; no runtime deployment, credentials, orders or capital effects.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-08-15T23:00:00+02:00
head: e32599fd577fe31f9eb0d4acbb211b82a71621ce
status: active
proven:
  - Owner explicitly applied the developer-Portal rules to the entire current Portal.
  - Issue #1555 records the architecture-reset decision and exact base develop@9dd5887e301ddfeec6df6a3b3e2da24a9ced850f.
  - DEVELOPER_QUANT_PORTAL_ARCHITECTURE.md has been created on the bounded architecture branch.
derived:
  - ADR-023 must supersede conflicting current-Portal mode/production assumptions while preserving historical evidence and proportional safety.
unknown:
  - terminal PR/CI result until the architecture PR is opened and validated
blockers: []
next_action: Update ARCHITECTURE_DECISIONS.md and ARCHITECTURE_REGISTRY.yaml, validate syntax/consistency, then open one PR to develop.
```
