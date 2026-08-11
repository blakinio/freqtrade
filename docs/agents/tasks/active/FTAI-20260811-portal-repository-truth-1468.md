---
task_id: FTAI-20260811-portal-repository-truth-1468
programme_id: FTAI-PROGRAM-AI-TRADING-PORTAL
project_lane: freqtrade-portal
status: validating
task_kind: ci_governance
priority: high
repository: blakinio/freqtrade
base_branch: develop
branch: docs/portal-repository-truth-1468
related_pr: 1469
issue: 1468
created: 2026-08-11
updated: 2026-08-11
live_capital_authorized: false
production_deployment_authorized: false
---

# Portal repository truth and CODEOWNERS drift guard

## Objective

Make `ai_platform/portal/README.md` and `.github/CODEOWNERS` reflect the exact current Portal implementation boundary without turning target architecture into implementation claims, and add a deterministic CI guard against the verified drift.

## Feature scope

```yaml
feature_scope:
  type: documentation
  user_facing: false
  backend_required: false
  frontend_required: false
  integration_required: true
  e2e_required: false
  completion_claim: internal_only
```

Runtime/browser E2E is `NOT_APPLICABLE`: no product/runtime/deployment behavior changes. Repository documentation build, `tests/ci`, exact-head required CI and independent review remain required.

## Acceptance

- stale `future/unimplemented` Portal wording is absent;
- README points current implementation claims to `tools/portal_audit/ledger/index.json` and architecture claims to `ARCHITECTURE_REGISTRY.yaml` / canonical Portal docs;
- README explicitly preserves PAPER-only / fail-closed LIVE authority;
- CODEOWNERS explicitly covers current control-plane, execution, identity, security, credentials, database, risk, contracts, web and Synology deployment roots;
- a network-free `tests/ci` guard detects recurrence;
- exact-final-head required CI and documentation build pass;
- independent review has zero open material findings before merge.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-08-11T09:08:00Z
head: 143d03850470a6e497d1d50595b97039284b3497
branch: docs/portal-repository-truth-1468
pr: 1469
status: validating
context_routes:
  - Portal repository truth
  - CI governance
owned_paths:
  - ai_platform/portal/README.md
  - .github/CODEOWNERS
  - tests/ci/test_portal_repository_truth.py
  - docs/agents/tasks/active/FTAI-20260811-portal-repository-truth-1468.md
proven:
  - develop@816aac5018b785f750ab9eaffd5de9033f988999 contains a living exact-head Portal completeness ledger.
  - the prior Portal README falsely described implemented Portal surfaces as future/unimplemented.
  - CODEOWNERS retained historical Portal backend/infra path-specific entries instead of current sensitive roots.
  - PR 1469 is the sole delivery PR for Issue 1468 and was zero commits behind develop when opened.
  - PAPER remains the only currently authorized operational mode and LIVE remains unreachable/fail-closed.
derived:
  - documentation truth must defer implementation completeness to exact-head evidence rather than package presence.
unknown:
  - exact-head CI result and independent review disposition for PR 1469.
conflicts: []
first_failure:
  marker: stale Portal implementation boundary documentation
  evidence: ai_platform/portal/README.md on develop@816aac5018b785f750ab9eaffd5de9033f988999
rejected_hypotheses:
  - treat stale README as harmless because architecture registry is canonical; rejected because root AGENTS routes Portal workers through this README.
changed_paths:
  - ai_platform/portal/README.md
  - .github/CODEOWNERS
  - tests/ci/test_portal_repository_truth.py
  - docs/agents/tasks/active/FTAI-20260811-portal-repository-truth-1468.md
validation:
  - command: exact file/state inspection on develop@816aac5018b785f750ab9eaffd5de9033f988999
    result: PASS
    evidence: verified stale README, living ledger and CODEOWNERS mismatch before mutation
  - command: branch compare at PR creation
    result: PASS
    evidence: docs/portal-repository-truth-1468 was ahead by 4 and behind by 0 versus develop
  - command: runtime/browser E2E
    result: NOT_APPLICABLE
    evidence: documentation and network-free CI-governance repair only
blockers: []
next_action: Collect exact-head CI and fresh independent review on PR 1469; repair only evidence-backed material findings, then merge and close out Issue 1468.
```

## Safety boundary

Documentation/CI-governance only. No deployment, protected environment, private exchange credentials, real order, withdrawal, model/strategy promotion or LIVE/live-capital authority is introduced.
