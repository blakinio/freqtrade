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
  - private repository visibility confirmed
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
search_first:
  - current develop, open PRs and exact owned-path conflicts
  - canonical implementation and tests before adding code
  - shared contract freeze commit and dependency state
---

# Owner-managed external staging lane

## Goal

Record real P11 acceptance only after the owner provides and authorizes the protected external environment.

## Evidence at Gate 0

Repository-side staging packages exist and PR #758 adds a read-only target preflight. Real Cloudflare, Synology, Authentik, Vault, DNS/TLS and protected-environment evidence is absent. Repository metadata currently reports public visibility.

## Deliverables

- Owner-approved Cloudflare Tunnel, DNS, Access, WAF, rate-limit and direct-origin-denial evidence.
- Protected GitHub environment and reachable isolated Synology target.
- Authentik test identity, MFA and recovery plus Vault and private-Freqtrade acceptance.
- Five-probe External E2E evidence stored without secrets.
- Repository visibility changed to private and verified.

## Non-negotiable boundaries

- Paper, shadow or dry-run only; no live-capital authority.
- No browser-to-Freqtrade, exchange or Vault path.
- No protected-holdout reuse and no changes to frozen thresholds `0.006/-0.009`.
- Stay inside exact `owned_paths`; stop on the first incompatible shared-contract requirement.
- Add tests at the same layer and merge only through normal green CI.

## Acceptance criteria

- Only real target evidence may change P11 from external action.
- No fixture or simulation result is described as production-like acceptance.
- No live-capital or withdrawal authority is introduced.

## Validation

Run narrow tests first, then all repository workflows required by the changed paths. Validate this task checkpoint before every handoff.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-30T10:55:00+02:00
head: 1d347a785eddc900f4484c30e06c3ab4e8851b29
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
  - Repository-side staging packages exist and PR #758 adds a read-only target preflight. Real Cloudflare, Synology, Authentik, Vault, DNS/TLS and protected-environment evidence is absent. Repository metadata currently reports public visibility.
derived:
  - The bounded implementation scope is restricted to 2 exact path entries.
unknown:
  - Exact implementation HEAD, PR number and CI run IDs until the worker starts.
conflicts: []
first_failure:
  marker: OWNER_RESOURCE_GATE
  evidence: The missing evidence depends on owner-controlled external accounts, secrets, devices, targets and repository settings and cannot be produced autonomously.
rejected_hypotheses:
  - An unchecked backlog box alone proves missing implementation.
  - A downstream worker may redefine shared contracts.
  - Repository fixtures may be described as real external acceptance.
changed_paths: []
validation:
  - command: python tools/agents/checkpoint.py <task-path> --require-checkpoint
    result: PASS
    evidence: Gate 0 validates this compact checkpoint before dispatch.
blockers:
  - Repository metadata reports visibility public.
  - Cloudflare, protected environment, Synology, Authentik, Vault and external test identity evidence is unavailable.
  - PR #758 is still open and owns the read-only real-target preflight.
next_action: Do not start until the owner explicitly authorizes the lane, makes the repository private, and supplies the listed external resources.
```
