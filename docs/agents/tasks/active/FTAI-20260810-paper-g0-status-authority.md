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

Implement G0 work item 5 from `PAPER_PLATFORM_IMPLEMENTATION_PLAN.md`: establish one explicit, CI-enforced authority hierarchy for architecture/document truth, exact-head implementation inventory, legacy/roll-up status views and GitHub work ownership. Reuse the living exact-head ledger delivered by PR #1150; do not reopen completed #1101 or rewrite its historical snapshot as current truth.

## Acceptance inventory

- `S1`: `ARCHITECTURE_REGISTRY.yaml` is explicitly architecture/document authority, not implementation-completeness authority.
- `S2`: `tools/portal_audit/ledger/index.json` is the sole current exact-head implementation inventory and keeps `mode: living_exact_head_gate`.
- `S3`: `FEATURE_COMPLETENESS_LEDGER.json`/`.md` are classified as the historical #1101 snapshot at fixed `as_of_sha` and immutable Git blob identity; the legacy embedded `status_authority: true` flag is compatibility metadata, not current authority.
- `S4`: `UI_DELIVERY_STATUS.md` and programme/roadmap status views are classified as validated roll-up, work-ownership roll-up, dependency plan or historical evidence rather than standalone implementation truth.
- `S5`: GitHub Issues are work ownership/acceptance units, never standalone implementation truth.
- `S6`: one machine-readable status-authority contract is referenced from the living ledger package.
- `S7`: deterministic network-free CI rejects missing authority paths, mismatched living-ledger schema/mode, unclassified legacy status surfaces, historical snapshot rewrite, duplicate current-authority markers/claims, an implicit second current implementation authority, or any structured LIVE/protected/deployment authority grant.
- `S8`: existing #1101 historical compatibility markers remain intact; historical evidence is not rewritten.
- `S9`: runtime/browser E2E is `NOT_APPLICABLE` because this package changes status/governance truth only.
- `S10`: fresh independent review, exact-head CI and zero unresolved review threads are required before merge.

## Repair history

- Initial exact-head CI on `96c753d4e38195ef77182924be4c26b9a382e1e7` failed because `tests/ci/test_portal_status_authority.py` was not ruff-formatted. This is an owned formatting defect.
- Independent Codex review on the same head found P1 `PRRT_kwDOTdDTU86YA3Gc`: competing status authorities were trusted from the sidecar allowlist instead of discovered; P1 `PRRT_kwDOTdDTU86YA3Gh`: #1101 identity compared two editable values instead of immutable content; and P2 `PRRT_kwDOTdDTU86YA3Gn`: human denial wording did not structurally prohibit authority grants.
- Repair cycle 1 addresses the full finding set together: repo-wide documentation discovery for the reserved current-authority marker/explicit claims and top-level `status_authority: true`; fixed #1101 `as_of_sha` plus independently computed Git blob SHA `4893b73ef020621529612192ff942fef79fb3cfc`; exact structured false-valued LIVE/real-capital/credential/promotion/protected/deployment grants; and formatter-compliant test layout.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-08-10T20:15:45Z
head: 9bc4bc61e13c87bbe628ee67b96b44bf10bd7c8d
branch: feat/paper-g0-status-authority-20260810
pr: 1449
status: validating
invocation_started_at: 2026-08-10T20:10:00Z
last_progress_at: 2026-08-10T20:15:45Z
ci_checks_for_current_head: 0
unchanged_state_checks: 0
review_checks_for_current_head: 0
identical_failure_retries: 0
repair_cycles_for_current_gate: 1
context_reconstruction_attempts: 0
stall_warnings: 0
context_routes:
  - G0 status authority
  - living exact-head portal audit ledger
  - legacy feature-completeness snapshot
  - fail-closed authority discovery
owned_paths:
  - docs/ai_platform/portal/IMPLEMENTATION_STATUS_AUTHORITY.md
  - docs/ai_platform/portal/UI_DELIVERY_STATUS.md
  - tools/portal_audit/ledger/index.json
  - tools/portal_audit/ledger/status_authority.json
  - tests/ci/test_portal_status_authority.py
  - docs/agents/tasks/active/FTAI-20260810-paper-g0-status-authority.md
proven:
  - G0 explicitly requires implementation-status authority and CI-enforced roll-up rules.
  - PR 1150 already delivered tools/portal_audit/ledger/index.json as a living exact-head gate.
  - The older FEATURE_COMPLETENESS_LEDGER snapshot remains at fixed as_of_sha b39b29c3e831ba491aa3376e5de86a8c09e2b537 and Git blob SHA 4893b73ef020621529612192ff942fef79fb3cfc.
  - The living index points to tools/portal_audit/ledger/status_authority.json.
  - The authority sidecar classifies architecture, living implementation truth, GitHub Issue ownership and every legacy #1101 status surface separately.
  - The sidecar now carries explicit false authority grants for LIVE trading, real capital, withdrawals, private trading credentials, model or strategy promotion, protected-environment mutation and production deployment.
  - UI_DELIVERY_STATUS retains its legacy marker for #1101 compatibility and one reserved living-ledger current-authority marker.
  - The CI guard discovers duplicate current-authority markers/explicit current-authority claims across docs, detects any additional documentation JSON top-level status_authority true, pins the #1101 content by Git blob identity, and validates structured safety grants.
  - PR 1449 remains the single delivery PR for this bounded G0 package and contains the same six declared changed paths.
derived:
  - The repair closes all three first-review findings without changing runtime, browser, deployment or trading behavior.
  - PAPER remains the only authorized operational mode and LIVE remains unreachable/fail-closed.
unknown:
  - Exact-head CI result on the successor created by this checkpoint update.
  - Fresh independent Codex disposition on that successor exact head.
conflicts:
  - none found with PR 1447 or the stacked isolation required by PR 1448
first_failure:
  marker: first candidate was formatter-invalid and did not independently discover competing authority or immutably pin #1101
  evidence: Freqtrade CI 31425929193 plus Codex threads PRRT_kwDOTdDTU86YA3Gc PRRT_kwDOTdDTU86YA3Gh PRRT_kwDOTdDTU86YA3Gn
rejected_hypotheses:
  - Reopen Issue 1101; rejected because it is completed and this is a later G0 authority migration over PR 1150.
  - Rewrite the historical feature ledger snapshot to the current head; rejected because that would falsify historical evidence.
  - Compare only snapshot metadata fields; rejected because two repository-controlled values can drift together.
  - Rely only on denial prose for LIVE/protected authority; rejected in favor of exact structured false-valued grants.
changed_paths:
  - docs/ai_platform/portal/IMPLEMENTATION_STATUS_AUTHORITY.md
  - docs/ai_platform/portal/UI_DELIVERY_STATUS.md
  - tools/portal_audit/ledger/index.json
  - tools/portal_audit/ledger/status_authority.json
  - tests/ci/test_portal_status_authority.py
  - docs/agents/tasks/active/FTAI-20260810-paper-g0-status-authority.md
validation:
  - command: initial exact-head CI on 96c753d4e38195ef77182924be4c26b9a382e1e7
    result: FAIL
    evidence: Freqtrade CI 31425929193; ruff format would reformat tests/ci/test_portal_status_authority.py; Risk-aware CI 31425929404 PASS; CodeQL 31425929192 PASS; zizmor 31425929249 PASS
  - command: independent Codex review of 96c753d4e38195ef77182924be4c26b9a382e1e7
    result: FAIL
    evidence: P1 PRRT_kwDOTdDTU86YA3Gc; P1 PRRT_kwDOTdDTU86YA3Gh; P2 PRRT_kwDOTdDTU86YA3Gn; all addressed by repair cycle 1 successor
  - command: runtime/browser E2E
    result: NOT_APPLICABLE
    evidence: status/governance-only package; no product runtime or browser behavior changes
blockers:
  - none before fresh exact-head CI and independent review of the successor created by this checkpoint update
next_action: Resolve live PR 1449 successor head, resolve the three reviewed threads as remediated, request fresh Codex review, and collect the first bounded exact-head CI observation. Remediate only a new material owned finding; if all gates are clear, archive the task in the same PR and validate the final archival successor before merge.
```
