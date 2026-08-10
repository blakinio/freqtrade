# FTAI-20260810 — PAPER G0 Implementation Status Authority

```yaml
task_id: FTAI-20260810-paper-g0-status-authority
programme_id: FTAI-PAPER-PLATFORM
repository: blakinio/freqtrade
project_lane: freqtrade-portal
task_kind: ci_governance
phase: validation
status: validating
priority: high
execution_mode: github_only
run_scope: autonomous_program
continuation_policy: continue_until_real_stop
base_branch: develop
trusted_base_sha: 5a19ae32f1f71b112130ea66cb8d56d9a3e44049
delivery_branch: feat/paper-g0-status-authority-20260810
delivery_pr: 1449
paper_gate: G0
live_capital_authorized: false
protected_production_deployment_authorized: false
```

## Objective

Implement G0 work item 5 from `PAPER_PLATFORM_IMPLEMENTATION_PLAN.md`: establish one explicit, CI-enforced authority hierarchy for architecture/document truth, exact-head implementation inventory, historical/roll-up status views and GitHub work ownership. Reuse PR #1150's living exact-head ledger and preserve completed #1101 JSON evidence as immutable history.

## Acceptance inventory

- `ARCHITECTURE_REGISTRY.yaml` remains architecture/document authority, not implementation-completeness authority.
- `tools/portal_audit/ledger/index.json` is the sole current exact-head implementation inventory and keeps `mode: living_exact_head_gate`.
- The #1101 JSON snapshot stays fixed at `b39b29c3e831ba491aa3376e5de86a8c09e2b537` / Git blob `4893b73ef020621529612192ff942fef79fb3cfc`.
- Legacy Markdown/roadmap/README surfaces are historical or validated roll-ups and explicitly point current claims to the living ledger.
- GitHub Issues remain work ownership/acceptance evidence, never standalone implementation truth.
- CI rejects duplicate reserved current-authority markers, legacy conflicting prose, competing tracked repository JSON `status_authority: true`, immutable #1101 drift, or structured LIVE/protected/deployment authority grants.
- Runtime/browser E2E is `NOT_APPLICABLE`: status/governance-only package.
- Fresh independent review, exact-head CI and zero unresolved material review threads are required before merge.

## Repair history

- Cycle 1: fixed sidecar-only discovery, immutable #1101 identity and prose-only safety denial after Codex `PRRT_kwDOTdDTU86YA3Gc`, `PRRT_kwDOTdDTU86YA3Gh`, `PRRT_kwDOTdDTU86YA3Gn`.
- Cycle 2: fixed task-record self-triggering, target-specific marker detection and ruff layout after Codex `PRRT_kwDOTdDTU86YBYXo`, `PRRT_kwDOTdDTU86YBYXq`, `PRRT_kwDOTdDTU86YBYXt`; formatter failure confirmed by Freqtrade `31428452203`.
- Cycle 3/3: fresh review on `56f35b2f522de5e62988ae40ac9d7acc668b3652` found P1 `PRRT_kwDOTdDTU86YBiDb` because README, historical ledger projection and roadmap still called #1101 current authority, and P1 `PRRT_kwDOTdDTU86YBiDe` because JSON authority scanning was limited to `docs/`. The final repair reconciles those three human surfaces to the living ledger while retaining legacy compatibility markers, scans every git-tracked JSON file for top-level `status_authority: true`, and updates the normative authority contract accordingly.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-08-10T20:47:00Z
head: 3dc76cf741ba5bd5d23cb8b86c43d430fde8545e
branch: feat/paper-g0-status-authority-20260810
pr: 1449
status: validating
invocation_started_at: 2026-08-10T20:10:00Z
last_progress_at: 2026-08-10T20:47:00Z
ci_checks_for_current_head: 0
review_checks_for_current_head: 0
unchanged_state_checks: 0
identical_failure_retries: 0
repair_cycles_for_current_gate: 3
context_reconstruction_attempts: 0
stall_warnings: 0
context_routes:
  - G0 status authority
  - living exact-head portal audit ledger
  - immutable #1101 JSON snapshot
  - reconciled legacy human status surfaces
  - fail-closed tracked JSON authority discovery
owned_paths:
  - docs/ai_platform/portal/DELIVERY_ROADMAP.md
  - docs/ai_platform/portal/FEATURE_COMPLETENESS_LEDGER.md
  - docs/ai_platform/portal/IMPLEMENTATION_STATUS_AUTHORITY.md
  - docs/ai_platform/portal/README.md
  - docs/ai_platform/portal/UI_DELIVERY_STATUS.md
  - tools/portal_audit/ledger/index.json
  - tools/portal_audit/ledger/status_authority.json
  - tests/ci/test_portal_status_authority.py
  - docs/agents/tasks/active/FTAI-20260810-paper-g0-status-authority.md
proven:
  - PR 1150 already delivered the living exact-head ledger package.
  - #1101 JSON snapshot remains fixed at as_of_sha b39b29c3e831ba491aa3376e5de86a8c09e2b537 and Git blob 4893b73ef020621529612192ff942fef79fb3cfc.
  - Machine authority grants remain false for LIVE, real capital, withdrawals, private credentials, model/strategy promotion, protected mutation and production deployment.
  - Reserved current-authority marker discovery is target-independent across the documentation tree.
  - README, FEATURE_COMPLETENESS_LEDGER.md and DELIVERY_ROADMAP.md now explicitly identify #1101 markers as compatibility metadata and point current implementation completeness to tools/portal_audit/ledger/index.json.
  - JSON authority discovery now derives repository scope from git-tracked JSON files rather than docs-only traversal.
  - The immutable #1101 JSON file itself was not modified by this package.
derived:
  - Repair cycle 3 addresses both fresh review P1 findings without touching runtime, browser, deployment or trading behavior.
  - PAPER remains the only authorized operational mode and LIVE remains unreachable/fail-closed.
unknown:
  - Exact-head CI result on the successor created by this checkpoint commit.
  - Fresh independent Codex disposition on that successor exact head.
conflicts:
  - none found with PR 1447 or stacked PR 1451
first_failure:
  marker: earlier candidates did not fully discover/reconcile competing authority claims and initially retained formatter-invalid test layout
  evidence: Freqtrade 31425929193 and 31428452203 plus Codex threads recorded in repair history
rejected_hypotheses:
  - Reopen completed Issue 1101; rejected because this is a later authority migration.
  - Rewrite the immutable #1101 JSON snapshot; rejected because that would falsify historical evidence.
  - Whitelist contradictory legacy prose; rejected in favor of reconciling the human projections to the living authority.
  - Scan only docs JSON; rejected because machine-readable competing authority can exist elsewhere in tracked repository sources.
changed_paths:
  - docs/ai_platform/portal/DELIVERY_ROADMAP.md
  - docs/ai_platform/portal/FEATURE_COMPLETENESS_LEDGER.md
  - docs/ai_platform/portal/IMPLEMENTATION_STATUS_AUTHORITY.md
  - docs/ai_platform/portal/README.md
  - docs/ai_platform/portal/UI_DELIVERY_STATUS.md
  - tools/portal_audit/ledger/index.json
  - tools/portal_audit/ledger/status_authority.json
  - tests/ci/test_portal_status_authority.py
  - docs/agents/tasks/active/FTAI-20260810-paper-g0-status-authority.md
validation:
  - command: initial exact-head CI
    result: FAIL
    evidence: Freqtrade 31425929193 formatter failure; Risk-aware 31425929404 PASS; CodeQL 31425929192 PASS; zizmor 31425929249 PASS
  - command: cycle-2 exact-head CI on cdcf9937aca79d9d79bc6ee63285230ecf5c4fa4
    result: FAIL
    evidence: Freqtrade 31428452203 formatter failure with exact ruff diff
  - command: independent Codex review of 56f35b2f522de5e62988ae40ac9d7acc668b3652
    result: FAIL
    evidence: P1 PRRT_kwDOTdDTU86YBiDb and P1 PRRT_kwDOTdDTU86YBiDe; addressed by final repair cycle 3
  - command: runtime/browser E2E
    result: NOT_APPLICABLE
    evidence: status/governance-only package; no runtime or browser behavior changes
blockers: []
next_action: Resolve the two cycle-3 review threads as remediated, request fresh Codex review and collect the first aggregate exact-head CI observation on the successor. Because repair_cycles_for_current_gate is 3, any new material finding requires a separate isolation task rather than another repair on this task.
```
