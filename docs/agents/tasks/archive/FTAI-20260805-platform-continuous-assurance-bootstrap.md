---
task_id: FTAI-20260805-platform-continuous-assurance-bootstrap
status: completed
branch: docs/platform-continuous-assurance-agents-20260805
base_branch: develop
base_sha: e9c04506f8dce9df26ae63006229e0d48f1f4209
created: 2026-08-05
updated: 2026-08-05
related_pr: "1243"
merge_commit: c33648acfd86a0352836498103857b601b5f486f
programme_lane: freqtrade-assurance
task_kind: documentation
execution_mode: github
run_scope: single_task
continuation_policy: stop_at_task_boundary
task_completion_policy: finalize_archive_and_continue
user_communication: terminal_only
owned_paths: []
required_reads:
  - AGENTS.md
  - AGENTS.override.md
  - docs/agents/AGENTS.md
  - docs/agents/PROMPTING_STANDARD.md
  - docs/agents/PROMPTING_HANDOVER.md
  - docs/agents/DELIVERY_COMPLETENESS_AND_CLOSEOUT.md
  - docs/agents/ANTI_STALL_AND_EXECUTION_BUDGET.md
---

# Bootstrap the AI Platform Continuous Assurance agents

## Terminal result

PR #1243 merged the continuous-assurance programme, exactly three canonical role prompts, the short-invocation registry, the assurance project lane, and the race-resistant Issue claim/lease protocol as `c33648acfd86a0352836498103857b601b5f486f`.

## Delivered behaviour

- The Assurance Auditor audits complete modules and real journeys, deduplicates findings, creates atomic labelled Issues, and may create a controlled draft bootstrap PR only for a proven wholly missing canonical module.
- The Repair Worker selects one ready Issue, acquires a unique machine-readable claim, verifies race ownership, implements a complete applicable vertical slice, validates it, and releases ownership on terminal closeout.
- The Architecture and CI Advisor reviews architecture, repository structure, dependency direction, CI/CD, deployment and operations, then creates deduplicated recommendations, Issues or ADR proposals without silently implementing runtime changes.
- Existing programme/type/priority/risk/state labels provide navigation. Machine-readable area, paths, dependencies and conflict groups provide deterministic grouping when optional `area:*` labels are unavailable.
- Parallel writers are capped at three and may run only on disjoint owned/shared paths and conflict groups.
- A claim uses `claim_id`, `session_id`, a 45-minute renewable lease, immediate re-read after claim, a durable task record, branch and draft PR. Assignee identity is supplementary, so same-account agents remain distinguishable.
- Stale takeover requires lease expiry, stale checkpoint, no live progress and no remaining runner/protected/uncommitted ownership.

## Closeout

```yaml
implementation_complete: true
vertical_slice_complete: true
outcome_verified: true
audit:
  result: PASS
  validator_role: fresh documentation and governance reviewer
  exact_head: 1792872aeeeb75c784797eef0fee0af85cde034a
  review_id: 4865064797
  material_findings_open: 0
e2e:
  result: NOT_APPLICABLE
  reason: documentation and agent-governance changes expose no runtime, trading or product UI journey
validation:
  project_lanes_json:
    result: PASS
    evidence: schema version 2 parsed with six lanes and freqtrade-assurance first
  exact_head_ci:
    head: 1792872aeeeb75c784797eef0fee0af85cde034a
    result: PASS
    required_checks:
      - Freqtrade CI run 31011780882
      - GitHub Actions Security Analysis with zizmor run 31011779902
      - Risk-aware component CI run 31011780124
pull_requests:
  terminal_prs:
    - blakinio/freqtrade#1243 merged as c33648acfd86a0352836498103857b601b5f486f
  unresolved_review_threads: 0
task_status: completed
task_archived: true
ownership_released: true
live_capital_operations: none
production_operations: none
```

## Owner commands now available

- `Uruchom audyt całej platformy autonomicznie.`
- `Uruchom agenta naprawczego platformy.`
- `Uruchom 3 agentów naprawczych platformy.`
- `Uruchom przegląd architektury i CI platformy autonomicznie.`

All longer instructions resolve from live repository state and the canonical prompt files.
