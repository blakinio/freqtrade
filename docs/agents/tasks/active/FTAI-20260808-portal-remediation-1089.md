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
  - tools/portal_audit/ledger/index.json
  - tools/portal_audit/ledger/runtime.json
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

Resolve #1089 by deploying the existing identity-enabled canonical Portal control plane in strict API mode with private PostgreSQL schema authority, durable migration/recovery, truthful fail-closed provider behavior, exact-image validation and a real authenticated Chromium journey, without widening runtime or live-capital authority.

## Repository result

- Canonical identity-enabled product API is the deployment composition root; production/staging fixture mode is rejected.
- `/healthz` and `/readyz` are separated; readiness proves database/schema/router composition.
- Synology deployment uses private digest-pinned PostgreSQL, explicit migrations, durable state transfer and copy-on-write rollback with source/candidate database identities recorded.
- Public API stays unprivileged; no Docker socket, exchange execution credentials, withdrawals or live-capital authority are introduced.
- Production image includes the full Portal runtime resources and pinned Strategy Lab numerical dependencies; exact-image validation executes a real research-only Strategy Lab experiment.
- Real Chromium API-mode CI uses HTTPS, persisted Portal identity + CSRF, backend-derived data and browser-originated dry-run mutation without request interception or fixture identity/data.
- WickHunter Market Evidence is tenant-gated and read-only; incomplete active runs and disabled principals fail closed.
- Canonical feature-completeness ledger removes #1089 from repository deployment blockers without inferring protected-target acceptance.
- The older static portal-audit ledger is also reconciled: the API-mode Synology deployment boundary is no longer classified fixture-only, and the expected backend-route fingerprint records the current 87-route source inventory after removal of duplicate source-level route declarations.

## Audit / review

Four material review findings were found and repaired:

1. Strategy Lab production `numpy`/`pandas` dependencies and exact-image route coverage.
2. PostgreSQL copy-on-write source/candidate database identities in recovery evidence.
3. Market Evidence active-run metadata required when no immutable package exists.
4. Market Evidence tenant preflight requires an active principal as well as active membership/role.

All four review threads are resolved. Fresh post-remediation inspection of the changed implementation and the corresponding reader/database contracts found no additional material repository finding.

The canonical completeness audit on exact head `eca3e9443f959ab7eb4118e4a4d1e0be7060dea7` reached its static inventory gate after all earlier component/closure jobs passed. Its only execution blocker was an explicit-ledger drift guard:

```yaml
backend_routes_expected: 92
backend_routes_actual: 87
backend_routes_actual_sha256: 47e9f7a441d06e9d0d67f43bd772930ccab22176b7711ec5331f876885ea7127
```

The route classification set remains the same; the count/digest includes source file identity and changed because the #1089 composition removed duplicate source-level route declarations. The audit ledger was explicitly versioned to `2026-08-09.1` and the stale `Full Portal Synology candidate|FIXTURE_ONLY|...#1089` runtime disposition was replaced by the repository-proven API-mode deployment disposition. Protected-target acceptance remains external.

## Supporting validation

Review-remediation head `bb67b46d73400700d65121d34ea5c5369e247297`:

```yaml
api_mode_browser_run: 31280937019
  result: PASS
portal_exact_image_supply_chain_run: 31280937026
  result: PASS
codeql_run: 31280937001
  result: PASS
zizmor_run: 31280937022
  result: PASS
risk_aware_component_ci: 31280937119
  exact_portal_image: PASS
  strategy_lab_exact_image_experiment: PASS
```

Exact head `eca3e9443f959ab7eb4118e4a4d1e0be7060dea7` additionally proved before the audit-ledger-only correction:

```yaml
api_mode_browser_run: 31281154319
  result: PASS
portal_exact_image_supply_chain_run: 31281154285
  result: PASS
codeql_run: 31281154292
  result: PASS
zizmor_run: 31281154303
  result: PASS
risk_aware_component_ci: 31281154396
  portal_web: PASS
  exact_portal_image: PASS
  ai_platform: PASS
  postgres_recovery: PASS
  closure_backend: PASS
  closure_chromium: PASS
  closure_exact_head_gate: PASS
  strategy_engine: PASS
  completeness_audit: LEDGER_DRIFT_ONLY
freqtrade_ci: 31281154310
  pre_commit: PASS
```

## Recovery checkpoint

```yaml
policy_version: 1
generation: 6
session_id: 20260808T233000+0200-owner-continuation
session_started_at: 2026-08-08T23:31:00+02:00
checkpointed_at: 2026-08-09T00:22:00+02:00
last_progress_at: 2026-08-09T00:22:00+02:00
phase: validation
exact_head_before_checkpoint_commit: c7676dd55aa3721b0d71fa172b9e6cc1e668c5c8
pull_request: 1393
active_operation: final exact-head GitHub Actions validation after explicit static-audit-ledger reconciliation
external_run_ids: []
operation_started_at: null
wait_deadline_at: null
check_generation: final-post-audit-ledger-fix-v1
checks_used: 0
status: active
safe_to_resume: true
resume_condition: current-head GitHub Actions expose an actionable result or terminal pass
next_action: Validate the final exact head. If the static completeness audit exposes another explicit ledger fingerprint, reconcile only grounded current inventory; otherwise require all terminal CI, develop synchronization, zero review threads/duplicates, archive this task, validate archive head, squash-merge #1393 and verify #1089 closure.
```

## Terminal conditions remaining

- required exact-head Freqtrade CI is green;
- Risk-aware component CI is green including Program Closure E2E, Strategy Engine, canonical Portal Completeness Audit and Universal Portal E2E;
- real Portal API Mode Browser, Portal Exact-Image Supply Chain, CodeQL and zizmor are green on the exact head;
- branch is not behind `develop`, no duplicate #1089 repair PR exists, and unresolved review threads are zero;
- task is archived and required archive-head CI is green;
- PR #1393 is squash-merged and Issue #1089 is closed;
- protected Synology target acceptance remains `NOT_CLAIMED` and live capital remains unauthorized.
