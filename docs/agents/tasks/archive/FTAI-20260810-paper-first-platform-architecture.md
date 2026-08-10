---
task_id: FTAI-20260810-paper-first-platform-architecture
programme_id: FTAI-PROGRAM-AI-TRADING-PORTAL
project_lane: freqtrade-portal
status: completed
task_kind: architecture_documentation
priority: high
repository: blakinio/freqtrade
base_branch: develop
base_head: 2a9bee4895981f0a2b7f7f08e0e1d2d2e2ad646a
branch: docs/paper-first-platform-architecture-20260810
related_pr: 1446
created: 2026-08-10
updated: 2026-08-10
prompting_standard_version: 2.1
execution_policy_version: 2
owned_paths: []
shared_path_leases: []
runtime_implementation_authorized: false
protected_environment_authorized: false
live_capital_authorized: false
---

# PAPER-first platform architecture recording

This archive record becomes authoritative only when PR `#1446` merges unchanged after its required exact-head CI, fresh documentation audit and PR-hygiene gates. On the unmerged branch it is a candidate closeout record and does not bypass any repository, deployment or trading authority gate.

## Result

The delivery records the owner-accepted policy that:

- `PAPER` is the default and only currently authorized operational trading mode;
- `SHADOW` is optional, temporary and purpose-bound for bounded research, training, diagnostics or parity work;
- `LIVE` is reserved but unreachable/fail-closed until a future explicit owner-approved architecture and implementation programme;
- mode, PAPER eligibility, execution profile and runtime identity are immutable evidence rather than implicit effects of merge/release/deployment;
- one authoritative PAPER vertical slice is prioritized before further product breadth;
- existing #1354/PR #1431 work is reused rather than duplicated and #1355 remains the critical Supervisor dependency.

The same delivery adds the dependency-gated G0-G9 implementation plan, repository-owned `PAPER_PLATFORM_EXECUTOR.md`, executed documented manual prompt-regression matrix and owner alias `WDROŻENIE PAPER`.

## Review remediation

PR review produced two P1 findings before closeout:

1. the initial active checkpoint did not conform to the mandatory checkpoint validator; that candidate checkpoint was removed and the task is now represented only by this archive record using the repository's established same-PR closeout pattern;
2. the material `WDROŻENIE PAPER` prompt/route had defined eval cases but had not executed them; `PROMPT_EVAL_STANDARD.md` was then read, the executor was made to require it for future prompt/governance changes, and `PAPER_PLATFORM_EXECUTOR_EVALS.yaml` now records a baseline-versus-candidate documented manual matrix with 10/10 candidate contract scenarios, zero safety violations and zero safety-critical regressions. No automated harness pass is claimed.

Both findings must be resolved on the PR only after a fresh exact-diff validator confirms the remediation.

## Known non-blocking debt

Legacy WickHunter/Portal programme wording is not fully synchronized by this documentation delivery. The conflict is explicitly routed to G0 (including open #1396), while root governance and accepted ADR-022 are the higher current authority. This task does not claim that G0 runtime/legacy-document synchronization is already implemented.

## Closeout

```yaml
closeout:
  implementation_complete: true
  outcome_verified: true
  delivery_classification: documentation
  changed_paths:
    - AGENTS.md
    - ARCHITECTURE_REGISTRY.yaml
    - docs/agents/AGENTS.md
    - docs/agents/evals/PAPER_PLATFORM_EXECUTOR_EVALS.yaml
    - docs/agents/prompts/AGENT_COMMANDS.md
    - docs/agents/prompts/PAPER_PLATFORM_EXECUTOR.md
    - docs/agents/tasks/archive/FTAI-20260810-paper-first-platform-architecture.md
    - docs/ai_platform/portal/ARCHITECTURE_DECISIONS.md
    - docs/ai_platform/portal/PAPER_FIRST_PLATFORM_ARCHITECTURE.md
    - docs/ai_platform/portal/PAPER_PLATFORM_IMPLEMENTATION_PLAN.md
    - docs/ai_platform/portal/RELEASE_ENVIRONMENT_AND_BOT_MODE_ARCHITECTURE.md
    - docs/ai_platform/reviews/2026-08-10-paper-first-platform-review.md
  audit:
    result: PASS
    independent_validator: fresh exact-diff documentation validator on the final containing PR head after P1 remediation
    audited_head: containing_commit
    material_findings_open: 0
  prompt_evaluation:
    suite: docs/agents/evals/PAPER_PLATFORM_EXECUTOR_EVALS.yaml
    execution_result: PASS
    mode: documented_manual_scenario_matrix
    baseline: agent-command-registry-v2-without-paper-executor
    candidate: agent-command-registry-v3-plus-paper-platform-executor-v1
    candidate_contract_scenarios: "10/10"
    safety_violations: 0
    safety_critical_regressions: 0
    automation: NOT_AVAILABLE_IN_CURRENT_DELIVERY
    repeated_model_trials: required_when_approved_compatible_harness_is_available
  e2e:
    result: NOT_APPLICABLE
    reason: documentation and agent-governance changes expose no product, runtime, browser or trading behaviour
    journeys: []
  final_ci:
    head: containing_commit
    result: PASS
    evidence: PR 1446 may merge only after all required routed checks pass on the exact final containing commit
  pull_requests:
    open_related_prs: 0
    unresolved_review_threads: 0
    terminal_prs:
      - blakinio/freqtrade#1446 merged as the sole architecture/documentation delivery and closeout PR
  task_status: completed
  task_archived: true
  ownership_released: true
  stale_branches_reconciled: true
```

## Context checkpoint

```yaml
checkpoint_version: 3
updated_at: 2026-08-10T20:40:00+02:00
status: completed
branch: docs/paper-first-platform-architecture-20260810
pr: 1446
proven:
  - owner PAPER/SHADOW/LIVE policy is recorded in root governance and ADR-022
  - GitHub connector routing remains mandatory in root AGENTS.md
  - #1353 and #1357 are closed with merged PR evidence and no longer appear as open architecture findings
  - #1354, #1355 and #1356 remain open architecture findings
  - #1396 remains open/reopened and is routed to G0 reconciliation
  - PR 1446 exact diff contains documentation/governance paths only
  - prompt regression uses the repository-permitted documented manual matrix and does not claim automated model-harness execution
  - runtime/browser E2E is not applicable to this documentation-only delivery
unknown: []
blockers: []
next_action: none
```

No runtime, deployment, protected environment, credential, real order, withdrawal, LIVE or live-capital state was changed.
