# FTAI-20260808 Portal Remediation — Issue 1089 (Archived)

```yaml
task_id: FTAI-20260808-portal-remediation-1089
programme_id: FTAI-20260803-portal-remediation
issue: 1089
repository: blakinio/freqtrade
lane: freqtrade-portal
task_kind: implementation
phase: closeout
status: completed
priority: high
prompting_standard_version: 2.1
execution_policy_version: 2
execution_mode: github_only
branch: repair/1089-portal-api-mode-deployment
base_branch: develop
base_head: b6f9e5a5b9ca90f01a216a6390012758c7ff62a7
validated_product_head: 4a94ba3a0aa109254a8165dd026cf1331920c3b0
post_archive_remediation_head: c6383d6891b68e605c4facb8d750747271ecf922
pr: 1393
claim_id: ftai-1089-20260808T194400Z-gpt56sol
ownership_released_on_merge: true
repository_work_remaining: false
external_acceptance_remaining: true
protected_target_acceptance: NOT_CLAIMED
live_capital_authorized: false
withdrawals_enabled: false
protected_production_deployment_authorized: false
```

## Objective

Resolve #1089 by deploying the existing identity-enabled canonical Portal control plane in strict API mode with private PostgreSQL schema authority, durable migration/recovery, truthful fail-closed provider behavior, exact-image validation and a real authenticated Chromium journey, without widening runtime or live-capital authority.

## Repository result

- The canonical identity-enabled product API is the deployment composition root; production/staging fixture data and fixture identity are rejected.
- `/healthz` is liveness-only and `/readyz` proves database connectivity, migration/schema revision and required product-router composition.
- Synology deployment uses private digest-pinned PostgreSQL, explicit migrations, bounded legacy SQLite transfer and copy-on-write PostgreSQL upgrades with durable source/candidate recovery identity.
- Candidate DB authority is journaled before exposure; rollback quiesces the candidate before authority restoration, and partial quiesce failure restores the previous public runtime.
- If post-promotion web verification fails after the previous web has been renamed to a backup, the copy-on-write guard identifies and restores that exact new backup before propagating the failure, leaving it stopped until the outer authority rollback safely restores runtime state.
- The public API remains unprivileged: no Docker socket, exchange execution credentials, Vault execution material, withdrawals or live-capital authority are introduced.
- The production control-plane image includes pinned Strategy Lab numerical dependencies and exact-image validation executes a real research-only experiment.
- Real Chromium API-mode validation uses HTTPS, persisted Portal identity/session + CSRF, backend-derived data and browser-originated dry-run mutation without request interception or fixture fallback.
- Dashboard and Strategy Lab POST-backed requests forward the canonical CSRF token and fail closed on malformed/missing state.
- WickHunter Market Evidence is tenant-gated and read-only. Deployment uses the canonical package verifier, pins the selected evidence run, mounts a verified v2 package together with its bound v1 base where applicable, preserves the active-v1 pointer, verifies traversal permissions and active-principal authorization, and orders date/version/revision components numerically so `r10` supersedes `r9`.
- Canonical feature-completeness and static audit ledgers were reconciled to repository-proven API-mode deployment state without inferring protected-target acceptance.

## Fresh review and audit

The repair was repeatedly challenged after implementation. Material findings repaired before closeout included:

1. missing Strategy Lab production numerical dependencies and exact-image route coverage;
2. incomplete PostgreSQL recovery identity and crash-safe authority journaling/rollback sequencing;
3. partial quiesce recovery that could otherwise leave the public web container stopped;
4. post-promotion verification recovery that could otherwise lose the previous web backup and leave the public Portal down;
5. Strategy Lab and dashboard CSRF forwarding through the authenticated composition;
6. incomplete/disabled-principal Market Evidence fail-closed behavior;
7. immutable-package semantic verification, nested traversal permissions and selected-run pinning;
8. v2 Market Evidence base-v1 visibility and active-v1 pointer preservation;
9. truthful authority-journal evidence;
10. numeric Market Evidence run ordering for multi-digit revisions.

All material inline review findings have an implementation and focused regression on the repair branch. The final post-archive remediation is `c6383d6891b68e605c4facb8d750747271ecf922` (`fix(portal): restore web backup after verification failure`). Terminal merge requires all review threads resolved and required CI green on the exact archive branch head containing this remediation.

## Pre-archive exact-head validation

Validated product head before task archival: `4a94ba3a0aa109254a8165dd026cf1331920c3b0`.

```yaml
freqtrade_ci:
  run: 31305888518
  result: PASS
risk_aware_component_ci:
  run: 31305888658
  result: PASS
  includes:
    - AI Platform tests/lint
    - exact Portal image migration/state-transfer/API-mode/restart
    - PostgreSQL concurrency/rollback/restore
    - Program Closure backend and Chromium journeys
    - exact-head closure gate
    - Strategy Engine complete validation
    - canonical Portal Completeness Audit
    - Universal Portal backend + Chromium E2E
portal_api_mode_browser:
  run: 31305888500
  result: PASS
portal_exact_image_supply_chain:
  run: 31305888504
  result: PASS
codeql:
  run: 31305888572
  result: PASS
zizmor:
  run: 31305888547
  result: PASS
```

The post-archive remediation is intentionally not inferred from those earlier runs. Its correctness is accepted only if required CI becomes terminal green on the final branch head that contains both the remediation and this archived record.

## Terminal checkpoint

```yaml
checkpoint_version: 3
updated_at: 2026-08-09T11:55:00+02:00
validated_product_head: 4a94ba3a0aa109254a8165dd026cf1331920c3b0
post_archive_remediation_head: c6383d6891b68e605c4facb8d750747271ecf922
branch: repair/1089-portal-api-mode-deployment
pr: 1393
status: completed
proven:
  - full authenticated canonical Portal control plane is deployable in strict API mode
  - production database authority is PostgreSQL-only with explicit migration and durable recovery
  - pre-archive exact-image and real Chromium API-mode acceptance pass
  - Market Evidence deployment boundary is integrity-verified, tenant-gated, read-only and deterministically pinned
  - post-promotion verification backup recovery has focused regression coverage on the branch
derived:
  - repository implementation for #1089 is complete subject to final exact archive-head CI
unknown:
  - protected Synology target acceptance, intentionally not claimed
conflicts: []
blockers: []
next_action: Require terminal green CI on the exact archive branch head containing c6383d6891b68e605c4facb8d750747271ecf922, zero unresolved review threads, develop synchronization and no duplicate #1089 PR; then squash-merge #1393, verify #1089 closure and confirm this archived record on develop.
```

## Safety / external acceptance

Protected Synology target acceptance remains **NOT_CLAIMED**. This closeout does not authorize or imply live trading, withdrawals, live capital, protected production deployment, or possession/use of production secrets.
