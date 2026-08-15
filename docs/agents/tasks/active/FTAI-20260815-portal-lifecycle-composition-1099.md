# FTAI-20260815 Portal lifecycle composition #1099

```yaml
task_id: FTAI-20260815-portal-lifecycle-composition-1099
issue: 1099
status: implementing
owner: chatgpt-gpt-5.6-sol
branch: fix/portal-lifecycle-composition-1099
base: bbe39128b8b94aab134a216542f94a3d65c6c949
mode: PAPER_ONLY
live_authority: false
codex_or_owner_paid_ai: false
feature_scope: full_stack
completion_claim: complete_feature
owned_paths:
  - ai_platform/portal/control_plane/**
  - ai_platform/portal/events/**
  - ai_platform/portal/execution/**
  - ai_platform/portal/runtime_supervisor/**
  - ai_platform/portal/lifecycle/**
  - ai_platform/portal/web/**
  - tests/ai_platform/portal/**
  - docs/agents/tasks/active/FTAI-20260815-portal-lifecycle-composition-1099.md
next_action: implement durable desired-state command ingress, outbox recovery, runtime worker composition, authoritative reconciliation and API/browser contract
```

## Acceptance inventory

- durable idempotent desired-state command identity with expected state/version fencing;
- transactional desired-state + audit + outbox publication;
- retry/backoff/poison isolation so one failing event cannot block unrelated tenants;
- narrow Runtime Supervisor UDS client; no direct container authority in ordinary worker;
- exact generation-bound provision/start/pause/stop with authoritative observed-state reconciliation;
- restart recovery without duplicate runtime creation/commands;
- frontend/BFF/backend contract alignment and desired/observed truth separation;
- focused/integration/restart tests, API-mode Chromium evidence, fresh audit and exact-head CI;
- PAPER-only; LIVE remains unreachable.

This record remains active until merge, audit, E2E, exact-head CI, related-PR hygiene and terminal archive are real.