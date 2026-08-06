# FTAI-CA-1294 — cryptography 50 security update

```yaml
task_id: FTAI-CA-1294-cryptography-50
programme_id: FTAI-20260805-platform-continuous-assurance
issue: 1294
status: completed
completion_activation: merge_of_pr_1297
claim_id: ftaica-1294-20260806T104000Z-gpt56a
owner: released
ownership_released: true
lease_expires_at: null
base_branch: develop
source_pr: 1291
source_pr_terminal_state: closed_superseded
repair_pr: 1297
branch: repair/1294-cryptography-50
priority: P1
risk: medium
feature_scope:
  type: infrastructure
  user_facing: false
  backend_required: false
  frontend_required: false
  integration_required: true
  e2e_required: false
  completion_claim: internal_only
owned_paths: []
shared_paths: []
conflict_groups: []
```

## Outcome

The repository now preserves `cryptography==50.0.0` and permits that reviewed security release through the existing package-specific `uv` exception mechanism while retaining the global one-week dependency age gate.

```toml
[tool.uv]
exclude-newer = "1 week"

[tool.uv.exclude-newer-package]
ccxt = false
cryptography = false
```

## Root cause

Exact failed installation jobs `92576870866` and `92576870872` proved that `uv` filtered `cryptography==50.0.0` because its publication timestamp (`2026-07-31T14:23:33.331Z`) was newer than the effective cutoff (`2026-07-30T08:41:01Z`). The failure was not caused by Python support, wheel availability or an observed transitive constraint conflict.

## Security applicability

```yaml
classification: UNKNOWN
direct_repository_reachability: NOT_FOUND
searched_symbols:
  - pkcs7_decrypt_der
  - PKCS7
  - cryptography.hazmat
reason: No direct repository call site was found. Absence of transitive deployment-dependency reachability was not proven, so a stronger non-applicability claim is not made.
```

## Delivery and PR hygiene

- PR #1297 is the single atomic repair vehicle.
- Dependabot PR #1291 was closed as superseded only after its unique version bump was preserved in #1297.
- PR #1290 remains an independent `aiohttp` update; #1297 is integrated first because it carries the P1 security update and is currently mergeable against `develop`.
- Runtime E2E is `NOT_APPLICABLE`: no user-facing journey or runtime behavior is added.

## Validation contract

The implementation candidate head `c28114db618acf0eccf5989b8d68295630632bf8` proved successful dependency installation, bounded core validation, pre-commit checks and risk-aware component CI. The archival move intentionally changes the PR head, so terminal merge authority remains conditioned on live verification that every required check succeeds on the exact final PR #1297 head, review threads remain zero and the final independent audit reports zero material findings.

```yaml
closeout:
  implementation_complete: true
  vertical_slice_complete: true
  security_applicability: UNKNOWN
  audit:
    result: LIVE_PR_GATE
    material_findings_open: 0
  e2e:
    result: NOT_APPLICABLE
    reason: dependency-resolution and supply-chain configuration change with no user-facing journey
  final_ci:
    result: LIVE_PR_GATE
    head: exact PR 1297 head at merge
    required_checks:
      - Freqtrade CI
      - Risk-aware component CI
      - CodeQL
      - zizmor
  pull_requests:
    terminal_prs:
      - "#1291 closed_superseded"
    delivery_pr: "#1297 merge_only_after_exact_head_gates"
    unresolved_review_threads_required: 0
  task_status: completed
  task_archived: true
  ownership_released: true
  stale_branches_reconciled: after_merge
```

## Terminal invariant

This archive becomes authoritative only through merge of PR #1297 after exact-head CI, independent audit, mergeability and review-thread gates pass. No production, deployment, credential, trading, withdrawal or live-capital authority is granted.
