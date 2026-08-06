# FTAI-CA-1101 — Portal completeness ledger

```yaml
task_id: FTAI-CA-1101-portal-completeness-ledger
programme_id: FTAI-20260805-platform-continuous-assurance
issue: 1101
status: implementing
claim_id: ftaica-1101-20260806T122000Z-gpt56a
owner: repair-worker-1101-20260806T122000Z
session_id: repair-session-1101-20260806T122000Z-gpt56a
claimed_at: 2026-08-06T12:20:00Z
lease_expires_at: 2026-08-06T13:05:00Z
base_branch: develop
base_head: 4473dfc166d83fe5e0ffba4045c0dcd967626d68
branch: repair/1101-portal-completeness-ledger
priority: P2
risk: medium
feature_scope:
  type: documentation_governance
  user_facing: false
  backend_required: false
  frontend_required: false
  integration_required: true
  e2e_required: false
  completion_claim: internal_only
owned_paths:
  - docs/ai_platform/portal/FEATURE_COMPLETENESS_LEDGER.json
  - docs/ai_platform/portal/FEATURE_COMPLETENESS_LEDGER.md
  - docs/ai_platform/portal/README.md
  - docs/ai_platform/portal/POST_P12_INTEGRATION_BACKLOG.md
  - docs/ai_platform/portal/UI_DELIVERY_STATUS.md
  - docs/ai_platform/portal/NEXT_WORK_AND_REPAIR_PLAN.md
  - docs/ai_platform/portal/DELIVERY_ROADMAP.md
  - tools/agents/check_portal_completeness_ledger.py
  - tests/tools/test_check_portal_completeness_ledger.py
  - docs/agents/tasks/active/FTAI-CA-1101-portal-completeness-ledger.md
shared_paths: []
forbidden_paths:
  - ai_platform/**
  - deploy/**
  - .github/workflows/**
  - pyproject.toml
  - requirements*.txt
conflict_groups:
  - portal-status-ledger
```

## Root cause

Portal status documents used several incompatible vocabularies and combined bounded repository
acceptance with runtime composition, fixture browser evidence, deployment and protected-target
acceptance. The continuing audit consequently found modules described as complete while their
canonical product paths remained disconnected, fixture-only or externally unaccepted.

## Implementation contract

- establish one machine-readable canonical status authority;
- cover every governed P/PI/BM/BMW package and every canonical user-facing route;
- use only the approved completeness vocabulary;
- separate the five evidence dimensions;
- link every open Portal audit Issue to a non-complete dimension;
- preserve former status documents as exact dated Git evidence;
- add a deterministic static validator and regression tests;
- change no product runtime, deployment, workflow, dependency or trading behavior.

## Validation plan

```yaml
focused:
  - python tools/agents/check_portal_completeness_ledger.py
  - pytest -q tests/tools/test_check_portal_completeness_ledger.py
required_exact_head:
  - Freqtrade CI
  - Risk-aware component CI
  - CodeQL
  - zizmor
e2e:
  result: NOT_APPLICABLE
  reason: documentation/status-governance repair with no user-facing runtime behavior
```

## Context checkpoint

```yaml
recovery:
  policy_version: 1
  generation: 1
  session_id: repair-session-1101-20260806T122000Z-gpt56a
  session_started_at: 2026-08-06T12:20:00Z
  checkpointed_at: 2026-08-06T12:26:00Z
  last_progress_at: 2026-08-06T12:26:00Z
  phase: implementation
  exact_head: pending-first-commit
  pull_request: none
  active_operation: none
  external_run_ids: []
  operation_started_at: null
  wait_deadline_at: null
  check_generation: null
  checks_used: 0
  status: active
  safe_to_resume: true
  resume_condition: claim remains unique and branch ownership is unchanged
  next_action: validate the ledger and open the dedicated delivery PR
```

## Safety boundary

This task changes status/evidence governance only. It cannot claim real Authentik, Cloudflare,
Vault, Synology, Freqtrade or exchange acceptance and cannot authorize deployment, credentials,
trading, withdrawals or live capital.
