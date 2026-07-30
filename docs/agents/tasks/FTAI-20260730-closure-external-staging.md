---
task_id: FTAI-20260730-closure-external-staging
status: blocked
branch: owner/closure-external-staging
base_branch: develop
created: 2026-07-30
updated: 2026-07-30
related_pr: null
dependencies:
  - explicit owner authorization
  - PR #758 terminal
  - approved external resources available
owned_paths:
  - docs/agents/tasks/FTAI-20260730-closure-external-staging.md
  - docs/ai_platform/portal/external-acceptance-evidence/**
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/tasks/FTAI-20260730-ai-program-closure-orchestration.md
  - docs/ai_platform/PROGRAM_CLOSURE_MATRIX.md
  - ai_strategy_engine/TASKS.md
  - docs/agents/programs/FTAI_AI_TRADING_PORTAL_PROGRAM.md
search_first:
  - current develop, open PRs and exact owned-path conflicts
  - canonical implementation and tests before adding code
  - shared contract/dependency state before editing
---

# Owner-managed external P11 staging lane

## Goal

Record real P11 acceptance only after the owner provides and authorizes the protected external environment.

## Deliverables

- Owner-approved Cloudflare Tunnel, DNS, Access, WAF, rate-limit and direct-origin-denial evidence.
- Protected GitHub environment and reachable isolated Synology target.
- Authentik test identity, MFA and recovery plus Vault/private-runtime acceptance.
- Five-probe External E2E evidence stored without secrets.

## Non-negotiable boundaries

- Paper, shadow or dry-run only; no live-capital authority.
- No browser-to-Freqtrade, exchange or Vault path.
- No protected-holdout reuse and no changes to frozen thresholds `0.006/-0.009`.
- Stay inside exact `owned_paths`; stop on the first incompatible shared-contract requirement.
- Add tests at the same layer and merge only through normal green CI.

## Acceptance criteria

- Only real target evidence may change P11 status.
- No fixture or simulation is described as production-like acceptance.
- No live-capital or withdrawal authority is introduced.

## Validation

Run narrow validation first, then all repository gates selected by affected paths. Open one focused PR, verify exact implementation HEAD, required CI and unresolved review threads, synchronize normally and merge only after green checks.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-30T11:35:00+02:00
head: 0208666d98849386e2f2d9acf534b13891e4afa2
branch: owner/closure-external-staging
pr: null
status: blocked
context_routes:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/tasks/FTAI-20260730-ai-program-closure-orchestration.md
  - docs/ai_platform/PROGRAM_CLOSURE_MATRIX.md
owned_paths:
  - docs/agents/tasks/FTAI-20260730-closure-external-staging.md
  - docs/ai_platform/portal/external-acceptance-evidence/**
proven:
  - Repository-side staging packages exist; PR #758 is read-only preflight only.
derived:
  - The missing evidence depends on owner-controlled external resources and authorization.
unknown:
  - Exact external resource identities and authorization.
conflicts: []
first_failure:
  marker: OWNER_RESOURCE_GATE
  evidence: The first missing evidence requires owner-controlled external accounts, identities, devices and protected targets.
rejected_hypotheses:
  - An unchecked backlog box alone proves missing implementation.
  - A downstream worker may redefine shared contracts or edit another owner path.
  - Repository fixtures may be described as real P11 acceptance.
changed_paths: []
validation:
  - command: python tools/agents/checkpoint.py <task-path> --require-checkpoint
    result: PASS
    evidence: Gate 0 validated this compact checkpoint against the repository governance contract.
blockers:
  - Cloudflare, protected environment, Synology, Authentik, Vault and external test identity evidence is unavailable.
  - PR #758 remains open.
next_action: Do not start until the owner explicitly authorizes the lane and supplies the listed real external resources.
```
