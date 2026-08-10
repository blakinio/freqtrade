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
- `S7`: deterministic network-free CI rejects missing authority paths, mismatched living-ledger schema/mode, unclassified legacy status surfaces, historical snapshot rewrite, every second reserved current-authority marker regardless of target, competing current-authority claims in Portal status-bearing documentation, or any structured LIVE/protected/deployment authority grant.
- `S8`: existing #1101 historical compatibility markers remain intact; historical evidence is not rewritten.
- `S9`: runtime/browser E2E is `NOT_APPLICABLE` because this package changes status/governance truth only.
- `S10`: fresh independent review, exact-head CI and zero unresolved review threads are required before merge.

## Repair history

- Initial exact-head CI on `96c753d4e38195ef77182924be4c26b9a382e1e7` failed because `tests/ci/test_portal_status_authority.py` was not ruff-formatted.
- Initial Codex review found P1 `PRRT_kwDOTdDTU86YA3Gc` for sidecar-only competing-authority discovery, P1 `PRRT_kwDOTdDTU86YA3Gh` for mutable #1101 identity comparison, and P2 `PRRT_kwDOTdDTU86YA3Gn` for prose-only safety denial. Repair cycle 1 added documentation discovery, fixed `as_of_sha` plus independently computed Git blob SHA `4893b73ef020621529612192ff942fef79fb3cfc`, and structured false-valued authority grants.
- Fresh Codex review of `cdcf9937aca79d9d79bc6ee63285230ecf5c4fa4` found P1 `PRRT_kwDOTdDTU86YBYXo`: scanning agent task records as product authority prose made the test self-fail; P1 `PRRT_kwDOTdDTU86YBYXq`: discovery matched only the expected complete marker instead of the reserved prefix; and P1 `PRRT_kwDOTdDTU86YBYXt`: ruff formatting was still not applied. CI independently confirmed the formatter failure in Freqtrade run `31428452203` / lightweight job `93585799918`, while the pre-commit job emitted the exact formatter diff.
- Repair cycle 2 applies the exact ruff layout from the pre-commit diff, scans the reserved marker prefix across all documentation independently of target, scans explicit authority prose only within Portal status-bearing documentation, keeps agent task/governance records non-authoritative, and preserves repo-wide JSON detection of any additional top-level `status_authority: true`.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-08-10T20:24:25Z
head: b7e423765567c2b1dc64227ba83c68fcc356bb0f
branch: feat/paper-g0-status-authority-20260810
pr: 1449
status: validating
invocation_started_at: 2026-08-10T20:10:00Z
last_progress_at: 2026-08-10T20:24:25Z
ci_checks_for_current_head: 0
unchanged_state_checks: 0
review_checks_for_current_head: 0
identical_failure_retries: 0
repair_cycles_for_current_gate: 2
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
  - The authority sidecar carries explicit false authority grants for LIVE trading, real capital, withdrawals, private trading credentials, model or strategy promotion, protected-environment mutation and production deployment.
  - The CI guard now detects the reserved current-authority prefix across the full docs tree independently of its target, detects any additional documentation JSON top-level status_authority true, and limits plain-language current-authority claims to actual Portal status-bearing product documentation so task evidence cannot self-trigger.
  - The formatter changes applied in repair cycle 2 are copied from the exact pre-commit diff emitted by run 31428452203.
  - PR 1449 remains the single delivery PR for this bounded G0 package and contains the same six declared changed paths.
derived:
  - Repair cycle 2 addresses all fresh review findings without changing runtime, browser, deployment or trading behavior.
  - PAPER remains the only authorized operational mode and LIVE remains unreachable/fail-closed.
unknown:
  - Exact-head CI result on the successor created by this checkpoint update.
  - Fresh independent Codex disposition on that successor exact head.
conflicts:
  - none found with PR 1447 or PR 1451 stacked isolation for PR 1448
first_failure:
  marker: first two candidate generations did not make discovery both fail-closed and non-self-triggering, and the repair retained formatter-invalid layout
  evidence: Freqtrade CI 31425929193 and 31428452203; Codex threads PRRT_kwDOTdDTU86YA3Gc PRRT_kwDOTdDTU86YA3Gh PRRT_kwDOTdDTU86YA3Gn PRRT_kwDOTdDTU86YBYXo PRRT_kwDOTdDTU86YBYXq PRRT_kwDOTdDTU86YBYXt
rejected_hypotheses:
  - Reopen Issue 1101; rejected because it is completed and this is a later G0 authority migration over PR 1150.
  - Rewrite the historical feature ledger snapshot to the current head; rejected because that would falsify historical evidence.
  - Compare only snapshot metadata fields; rejected because two repository-controlled values can drift together.
  - Rely only on denial prose for LIVE/protected authority; rejected in favor of exact structured false-valued grants.
  - Treat agent task records as product status surfaces; rejected because they quote acceptance/evidence and cannot independently grant implementation authority.
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
    evidence: Freqtrade CI 31425929193 formatter failure; Risk-aware CI 31425929404 PASS; CodeQL 31425929192 PASS; zizmor 31425929249 PASS
  - command: independent Codex review of 96c753d4e38195ef77182924be4c26b9a382e1e7
    result: FAIL
    evidence: P1 PRRT_kwDOTdDTU86YA3Gc; P1 PRRT_kwDOTdDTU86YA3Gh; P2 PRRT_kwDOTdDTU86YA3Gn; addressed by repair cycle 1
  - command: exact-head lightweight/pre-commit checks on cdcf9937aca79d9d79bc6ee63285230ecf5c4fa4
    result: FAIL
    evidence: Freqtrade CI 31428452203; lightweight job 93585799918 and pre-commit formatter diff
  - command: independent Codex review of cdcf9937aca79d9d79bc6ee63285230ecf5c4fa4
    result: FAIL
    evidence: P1 PRRT_kwDOTdDTU86YBYXo; P1 PRRT_kwDOTdDTU86YBYXq; P1 PRRT_kwDOTdDTU86YBYXt; addressed by repair cycle 2 successor
  - command: runtime/browser E2E
    result: NOT_APPLICABLE
    evidence: status/governance-only package; no product runtime or browser behavior changes
blockers:
  - none before fresh exact-head CI and independent review of the successor created by this checkpoint update
next_action: Resolve live PR 1449 successor exact head, resolve the three repair-cycle-2 review threads as remediated, request fresh Codex review, and collect the first bounded exact-head CI observation. A third repair cycle is the final allowed cycle for this gate; if the successor is clear, archive this task in the same PR and validate the archival successor before merge.
```
