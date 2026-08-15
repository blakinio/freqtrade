---
task_id: FTAI-20260815-portal-developer-platform-reset-1555
status: waiting
repository: blakinio/freqtrade
lane: freqtrade-portal
related_issue: 1555
pull_request: 1558
branch: docs/portal-developer-platform-reset-20260815
base_head: 9dd5887e301ddfeec6df6a3b3e2da24a9ced850f
owner: chatgpt
task_kind: architecture
phase: final_ci
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
next_action: After PR #1558 exact-head CI becomes terminal, verify all required gates and changed paths; merge through branch protection/auto-merge only when green, then reclassify Portal/WickHunter backlog under ADR-023.
---

# Portal developer-platform architecture reset

## Objective

Persist the owner's 2026-08-15 decision that the **entire current Portal** is a private single-owner developer/quant/research platform operating on real public market data, simulation and local model development, rather than a production trading control plane organized around SHADOW/PAPER/LIVE.

## Scope

Owned paths:

- `docs/ai_platform/portal/ADR-023_DEVELOPER_QUANT_PORTAL.md`
- `docs/ai_platform/portal/DEVELOPER_QUANT_PORTAL_ARCHITECTURE.md`
- `ARCHITECTURE_REGISTRY.yaml`
- this task record

`docs/ai_platform/portal/ARCHITECTURE_DECISIONS.md` is preserved unchanged as the historical accepted log through ADR-022. ADR-023 is a dedicated accepted-decision extension registered by `ARCHITECTURE_REGISTRY.yaml`, which explicitly supersedes conflicting current-Portal assumptions while preserving historical decision text.

No product/runtime code mutation is part of this task.

## Acceptance

- [x] ADR-023 is recorded as owner-accepted and explicitly applies to the whole current Portal.
- [x] Conflicting current-Portal assumptions in ADR-003/004/005/013/014/016/017/020/021/022 are explicitly scoped/superseded without rewriting historical evidence.
- [x] The canonical developer Portal vocabulary is durable: `REALTIME_PUBLIC | REPLAY`, `LOCAL | SYNOLOGY`, integrated simulation, `BASELINE | CHALLENGER | ACTIVE | ARCHIVED`.
- [x] Real-money exchange execution is out of current product scope and requires a separate future Execution/Capital Gateway decision if ever desired.
- [x] `ARCHITECTURE_REGISTRY.yaml` names ADR-023 as the latest current Portal product overlay and marks old PAPER-first/mode architecture as superseded for current Portal scope.
- [x] Backlog migration requires `KEEP_NOW | SIMPLIFY | DEFER | OBSOLETE` reclassification from exact live state before code removal.
- [x] Documentation does not claim code migration complete.
- [x] Exact PR changed paths are limited to the four intended architecture/task files.
- [ ] Exact-head repository CI is terminal green.
- [ ] PR #1558 is merged; no runtime deployment, credentials, orders or capital effects.

## Context checkpoint

```yaml
checkpoint_version: 3
updated_at: 2026-08-15T23:08:00+02:00
head: 7ce47b71369952ca83e08e742cff749771cd092e
pull_request: 1558
status: waiting
ci_checks_for_current_head: 2
unchanged_state_checks: 0
proven:
  - Owner explicitly applied the developer-Portal rules to the entire current Portal.
  - Issue #1555 records the architecture-reset decision and exact base develop@9dd5887e301ddfeec6df6a3b3e2da24a9ced850f.
  - ADR-023 dedicated accepted-decision extension exists and contains an explicit supersession matrix.
  - DEVELOPER_QUANT_PORTAL_ARCHITECTURE.md defines the whole-Portal current target and user-workflow completion rule.
  - ARCHITECTURE_REGISTRY.yaml names ADR-023 as latest architecture change and Developer Quant Portal Architecture as canonical current target state.
  - Historical ARCHITECTURE_DECISIONS.md remains intact through ADR-022; registry authority records ADR-023 as the current extension.
  - PR #1558 is mergeable and changes exactly four intended paths.
  - zizmor exact-head run 31908426710 passed.
  - Auto-merge is enabled on PR #1558 and cannot merge before repository gates pass.
unknown:
  - terminal result of Freqtrade CI 31908426668
  - terminal result of CodeQL 31908426670
  - terminal result of Risk-aware component CI 31908426797
blockers:
  - exact-head CI is still queued/in progress
next_action: Refetch PR #1558 only after CI has materially advanced; if all required exact-head gates are green, allow/perform normal protected merge, then start exact-live-state backlog reclassification under ADR-023.
```
