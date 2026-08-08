# FTAI-20260808 Portal Remediation — Issue 1089

```yaml
task_id: FTAI-20260808-portal-remediation-1089
programme_id: FTAI-20260803-portal-remediation
issue: 1089
repository: blakinio/freqtrade
lane: freqtrade-portal
task_kind: implementation
phase: validation
status: validating
priority: high
prompting_standard_version: 2.1
execution_policy_version: 2
context_pressure: medium
decomposition_decision: phased_single_issue
execution_mode: github_only
run_scope: single_task
continuation_policy: continue_until_real_stop
task_completion_policy: finalize_archive
user_communication: terminal_only
claim_id: ftai-1089-20260808T194400Z-gpt56sol
feature_scope:
  type: authenticated_deployment_composition
  user_facing: true
  backend_required: true
  frontend_required: true
  integration_required: true
  e2e_required: true
branch: repair/1089-portal-api-mode-deployment
base_branch: develop
base_head: 3f60af82000cac47baa0a3a4302603eb1522363f
pr: 1393
owned_paths:
  - .github/workflow-registry.yaml
  - .github/workflows/portal-api-mode-browser.yml
  - .github/workflows/portal-schema-exact-image.yml
  - ai_platform/portal/database/transfer.py
  - ai_platform/portal/identity/public_runtime.py
  - deploy/synology/portal-oidc/Dockerfile.control-plane
  - deploy/synology/portal-oidc/deploy.py
  - deploy/synology/portal-oidc/deploy_entrypoint.py
  - deploy/synology/portal-oidc/market_evidence_runtime.py
  - deploy/synology/portal-oidc/postgresql_copy_on_write.py
  - deploy/synology/portal-oidc/requirements.txt
  - deploy/synology/portal/Dockerfile
  - docs/ai_platform/portal/ISSUE_1089_MARKET_EVIDENCE_RUNTIME.md
  - tests/ai_platform/portal/database/test_state_transfer.py
  - tests/ai_platform/portal/deployment/test_portal_oidc_market_evidence_runtime.py
  - tests/ai_platform/portal/deployment/test_portal_oidc_postgresql_copy_on_write.py
  - tests/ai_platform/portal/deployment/test_portal_oidc_public_deploy.py
  - tests/ai_platform/portal/identity/test_public_runtime_composition.py
  - tools/portal_schema/api_mode_browser_acceptance.sh
  - docs/agents/tasks/active/FTAI-20260808-portal-remediation-1089.md
shared_paths:
  - docs/ai_platform/portal/FEATURE_COMPLETENESS_LEDGER.json
  - docs/ai_platform/portal/FEATURE_COMPLETENESS_LEDGER.md
shared_path_leases: []
conflict_avoidance:
  - PR 1388 owns ai_platform/portal/control_plane/api.py, ai_platform/portal/control_plane/models.py, ai_platform/portal/database/schema.py and related runtime-generation paths; this repair does not modify those paths.
repository_work_remaining: false
external_acceptance_remaining: true
live_capital_authorized: false
withdrawals_enabled: false
protected_production_deployment_authorized: false
```

## Objective

Resolve Issue #1089 by deploying the existing identity-enabled canonical Portal control plane in strict API mode, with private PostgreSQL schema authority, durable migration/recovery, truthful fail-closed provider behavior, exact-image validation and a real authenticated browser journey. Do not create a second Portal API architecture and do not widen runtime or live-capital authority.

## Implemented repair

- `ai_platform.portal.identity.public_runtime` composes the existing identity-enabled canonical product API and separates `/healthz` liveness from `/readyz` database/schema/router readiness.
- Production rejects SQLite and insecure identity transport.
- Portal web defaults to API mode and rejects fixture data/fixture identity in staging and production.
- The Synology package provisions digest-pinned private PostgreSQL without a published database port, applies versioned migrations explicitly and promotes a candidate only after readiness and public probes pass.
- Legacy SQLite state is integrity-checked and transferred offline; existing PostgreSQL revisions use copy-on-write backup/quiesce/clone/migrate/readiness with the previous database retained for rollback.
- PostgreSQL copy-on-write recovery evidence persists both source and candidate database identities, so the immediate rollback target is unambiguous after repeated revisions.
- The public control-plane container remains unprivileged and receives no container-engine socket, exchange execution credentials or live-capital authority.
- Exact-image CI proves PostgreSQL migration/state transfer, canonical authenticated read plus dry-run mutation, unauthenticated fail-closed behavior, API mode, restart persistence and a real Strategy Lab experiment path that forces the production numerical runtime dependencies to load.
- Real Chromium API-mode CI uses HTTPS, a persisted Portal identity session and CSRF token, backend-derived `/bots` data, browser-originated dry-run bot creation through the Next BFF and refresh persistence, with no request interception or fixture identity/data.
- WickHunter Market Evidence is composed into the authenticated deployment using a tenant-gated, read-only host package mount with integrity/freshness checks and no fixture fallback; active runs without an immutable package must contain the reader-required incremental/request metadata, and tenant authorization requires both an active membership and active principal.
- The canonical completeness ledger removes #1089 from repository deployment blockers while retaining unrelated blockers and separate protected-target acceptance.

## Acceptance state

- [x] Existing identity-enabled full canonical Portal API is the deployed composition root.
- [x] Identity/session and product routes use backend identity-derived tenant context.
- [x] Liveness and readiness are separate; readiness validates database/schema/router composition.
- [x] Staging/production rejects fixture mode and requires API-mode server-side control-plane routing.
- [x] Private PostgreSQL migration, durable state preservation, restart and rollback contracts are explicit.
- [x] Public API remains unprivileged and private execution/provider authority remains server-side.
- [x] Market Evidence production runtime is tenant-gated, integrity-checked, read-only and fixture-free.
- [x] Real authenticated Chromium API-mode E2E exists with no request interception or fixture identity/data.
- [x] Canonical completeness ledger reconciles Issue #1089 without inferring protected-target acceptance.
- [x] Repair branch was merge-forwarded to `develop` with `behind_by: 0` before the review-remediation cycle.
- [x] Four current review findings were remediated in repository code/tests: Strategy Lab production dependencies + exact-image route exercise, PostgreSQL rollback database identities, fail-closed active Market Evidence metadata, and active-principal tenant preflight.
- [ ] Fresh independent post-remediation diff audit has zero material findings.
- [ ] Required repository workflows pass on the exact post-remediation head.
- [ ] Canonical Portal Completeness Audit and real API-mode browser gate pass on the exact post-remediation head.
- [ ] All four review threads are replied to and resolved; no duplicate repair PR owns #1089.
- [ ] Task is archived, ownership released on merge and archive-head CI passes.

## Validation evidence

Repository evidence already green on implementation head `b39b29c3e831ba491aa3376e5de86a8c09e2b537` before closeout-only ledger/synchronization commits:

```yaml
api_mode_browser_run: 31280088576
portal_exact_image_supply_chain_run: 31280088574
codeql_run: 31280088569
zizmor_run: 31280088604
protected_target_acceptance: NOT_CLAIMED
live_capital_authorized: false
```

Those runs are supporting evidence only. The earlier zero-finding audit was superseded by four current PR review findings; all four have now been remediated, but terminal acceptance requires a fresh post-remediation audit and exact-head gates.

## Review remediation checkpoint

```yaml
review_threads_detected: 4
strategy_lab_runtime_dependencies:
  status: remediated
  dependencies:
    - numpy==2.4.6
    - pandas==3.0.3
  exact_image_route: POST /v1/strategy-lab/experiments
  safety:
    research_only: true
    order_submission_performed: false
postgresql_copy_on_write_recovery_identity:
  status: remediated
  report_fields:
    - source_database
    - candidate_database
market_evidence_active_run_readiness:
  status: remediated
  active_run_required_files:
    - incremental-state.json
    - run-request.json
market_evidence_principal_status:
  status: remediated
  membership_status: active
  principal_status: active
```

## Recovery checkpoint

```yaml
policy_version: 1
generation: 4
session_id: 20260808T233000+0200-owner-continuation
session_started_at: 2026-08-08T23:31:00+02:00
checkpointed_at: 2026-08-09T00:07:00+02:00
last_progress_at: 2026-08-09T00:07:00+02:00
phase: validation
exact_head_before_checkpoint_commit: c73c39131adf6ba8e2d24afac2f0907bf8d92e4e
pull_request: 1393
active_operation: post-review-remediation independent audit and final exact-head GitHub Actions validation
external_run_ids: []
operation_started_at: null
wait_deadline_at: null
check_generation: post-review-remediation-v1
checks_used: 0
status: active
safe_to_resume: true
resume_condition: post-remediation audit or current-head GitHub Actions expose an actionable result
next_action: Re-audit the four remediated findings and surrounding diff, confirm develop synchronization, then inspect one aggregate exact-head CI snapshot and repair only actionable failures.
```

## Context checkpoint

```yaml
checkpoint_version: 6
updated_at: 2026-08-09T00:07:00+02:00
status: validating
branch: repair/1089-portal-api-mode-deployment
base_head: 3f60af82000cac47baa0a3a4302603eb1522363f
head_before_checkpoint_commit: c73c39131adf6ba8e2d24afac2f0907bf8d92e4e
pr: 1393
ci_checks_for_current_head: 0
unchanged_state_checks: 0
identical_failure_retries: 0
repair_cycles_for_current_gate: 1
context_reconstruction_attempts: 1
stall_warnings: 0
proven:
  - authenticated canonical API composition and tenant isolation
  - strict staging/production API mode with fixture rejection
  - private PostgreSQL migration/readiness/state-transfer/recovery boundary
  - PostgreSQL rollback source/candidate identities persisted in recovery metadata
  - unprivileged public API and preserved dry-run/non-live safety boundary
  - exact-image API-mode/restart evidence on the earlier implementation head
  - Strategy Lab production runtime dependencies are pinned and its create-experiment route is now exercised by exact-image validation
  - real authenticated Chromium API-mode read and dry-run mutation evidence on the earlier implementation head
  - authenticated tenant-gated Market Evidence deployment composition
  - Market Evidence active-run metadata and active-principal preflights now fail closed
  - canonical ledger reconciliation for Issue 1089 without protected-target inference
unknown:
  - fresh independent post-remediation audit outcome
  - exact-head CI outcome after review remediation
  - exact-head completeness-audit outcome after review remediation
  - final archive-head CI outcome
  - protected Synology target acceptance outcome, which remains separate and is not inferred
conflicts:
  - PR 1388 retains ownership of control-plane API/schema/model runtime-generation paths
blockers: []
next_action: Re-audit, validate exact head, resolve review threads only with grounded evidence, archive, rerun archive-head CI, then squash-merge the verified head and close Issue 1089.
```
