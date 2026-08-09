# FTAI-20260809 — Portal runtime storage isolation

```yaml
task_id: FTAI-20260809-portal-runtime-storage-isolation-1353
programme_id: FTAI-PROGRAM-AI-TRADING-PORTAL
repository: blakinio/freqtrade
issue: 1353
lane: freqtrade-portal
task_kind: implementation
phase: implement
status: implementing
priority: high
prompting_standard_version: 2.1
execution_policy_version: 2
context_pressure: medium
decomposition_decision: phased
execution_mode: github_only
run_scope: autonomous_program
continuation_policy: continue_until_real_stop
task_completion_policy: finalize_archive_and_continue
user_communication: terminal_only
feature_scope:
  type: infrastructure
  user_facing: false
  backend_required: true
  frontend_required: false
  integration_required: true
  e2e_required: true
  completion_claim: internal_only
base_branch: develop
trusted_base_sha: 39d741061a9f2ca17259d85609e83ca46b94f28f
branch: fix/portal-runtime-storage-isolation-1353
pr: none
related_issues:
  - 1354
  - 1355
  - 1413
related_prs:
  - 1367
  - 1395
  - 1416
live_capital_authorized: false
production_deployment_authorized: false
```

## Objective

Implement the ADR-020 trust/storage split for Portal-managed dry-run runtimes so Freqtrade cannot mutate Portal-authoritative identity evidence or canonical runtime inputs, durable Freqtrade state is generation-scoped, and runtime replacement cannot silently reuse or redefine an old generation.

## Owned paths

- `ai_platform/portal/execution/**`
- `tests/ai_platform/portal/execution/**`
- task-specific Portal execution integration/E2E tests when required
- this task record

Do not implement #1354 hard resource/network/process isolation or #1355 Runtime Supervisor authority in this task except where a minimal interface shape is required to preserve the accepted storage boundary.

## Acceptance inventory

- Freqtrade cannot modify Portal-authoritative runtime manifest/generation evidence.
- Canonical config is mounted read-only for one exact RuntimeGeneration and is not stored in a runtime-writable directory.
- Durable runtime DB/state is physically separate, generation-scoped and explicitly selected by `db_url`.
- Runtime manifest/control evidence is never mounted into Freqtrade.
- Replacement uses a distinct generation/runtime identity; old generation state/evidence remains historical and cannot become current implicitly.
- Replacement is fail-closed unless the previous generation is stopped/missing; no magical auto-replace.
- Lifecycle/private-read operations resolve only the current control-owned generation record.
- Restart/recovery reuses the same generation-scoped durable state without allowing runtime state to redefine control identity.
- Path derivation is deterministic from trusted identities and resists traversal/path escape by never using raw IDs as filesystem path components.
- Tests prove mount separation/read-only config/manifest absence, explicit persistent DB path, replacement semantics and stale-generation rejection.
- Exact-head required CI and relevant Portal API-mode/component integration pass.
- No live capital, private exchange credentials, public Freqtrade exposure, production deployment, #1354 resource/network hardening or #1355 Supervisor authority.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-08-09T18:12:00Z
head: 39d741061a9f2ca17259d85609e83ca46b94f28f
branch: fix/portal-runtime-storage-isolation-1353
pr: none
status: implementing
context_routes:
  - docs/ai_platform/portal/RUNTIME_ISOLATION_AND_SUPERVISOR_CONTRACT.md sections 10-11
  - issue 1353 and ADR-020
owned_paths:
  - ai_platform/portal/execution/**
  - tests/ai_platform/portal/execution/**
proven:
  - current driver mounts one runtime workspace read-write at /freqtrade/user_data
  - current workspace stores config.json and runtime-manifest.json together
  - dry-run config does not set db_url, leaving trade DB in the container writable layer
  - control plane now persists immutable RuntimeGeneration and BotInstance exposes desired_runtime_generation_id/observed_runtime_generation_id
  - no overlapping 1353 implementation PR or branch exists
  - issue 1353 remains open implementation work after accepted ADR-020
  - issue 1137 has released repository ownership and owns no paths
  - issues 1354 and 1355 remain separate follow-up boundaries
derived:
  - execution adapter must bind provisioning to the trusted desired RuntimeGeneration identity rather than stable tenant+bot identity alone
  - storage must be split into control evidence, immutable input and generation-local durable state roots
unknown:
  - exact final component/E2E routing after changed paths are committed
conflicts: []
first_failure:
  marker: runtime writable mount contains trusted config/manifest and DB persistence is implicit container-layer state
  evidence: ai_platform/portal/execution/workspace.py, driver.py, config.py
rejected_hypotheses:
  - relying on host UID ownership is sufficient; rejected by ADR-020 trust-boundary requirements
changed_paths:
  - docs/agents/tasks/active/FTAI-20260809-portal-runtime-storage-isolation-1353.md
validation:
  - command: live repository preflight and overlap inventory
    result: PASS
    evidence: develop@39d741061a9f2ca17259d85609e83ca46b94f28f; issue #1353; no implementation PR/branch for 1353
blockers:
  - none
next_action: Implement generation-scoped control/input/state paths, explicit durable db_url, read-only config mount and current-generation replacement fencing with focused tests.
```
