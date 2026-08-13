# FTAI-20260813 — G0 classified status-surface authority repair

```yaml
task_id: FTAI-20260813-paper-g0-classified-surface-authority-1501
programme_id: FTAI-PAPER-PLATFORM
repository: blakinio/freqtrade
issue: 1501
continuation_pr: 1449
base_branch: develop
delivery_branch: feat/paper-g0-status-authority-20260810
paper_gate: G0
status: waiting
priority: high
execution_mode: github_only
run_scope: single_task
continuation_policy: stop_at_task_boundary
live_capital_authorized: false
protected_production_deployment_authorized: false
invocation_started_at: 2026-08-13T08:58:00+02:00
last_progress_at: 2026-08-13T09:14:00+02:00
ci_checks_for_current_head: 0
pre_checkpoint_head_ci_observations: 3
unchanged_state_checks: 1
identical_failure_retries: 0
repair_cycles_for_current_gate: 1
context_reconstruction_attempts: 0
stall_warnings: 1
```

## Objective

Close fresh audit finding `G0-AUTH-20260813-01` on existing PR #1449 without creating another PR. Fail-closed prose discovery must inspect every text status-bearing surface classified by `tools/portal_audit/ledger/status_authority.json`, while preserving discovery of newly introduced Portal status documents.

## Finding and disposition

`G0-AUTH-20260813-01 / P1 / material merge blocker` — **REPAIRED**.

The prior guard searched current-authority prose only under `docs/ai_platform/portal/`, even though the machine contract classifies status-bearing surfaces outside that subtree, including `docs/agents/programs/FTAI_PORTAL_REMEDIATION_PROGRAM.md`. A classified external roll-up could therefore reintroduce a contradictory current implementation authority claim without failing CI.

`tests/ci/test_portal_status_authority.py` now:

- derives classified text status paths from machine-readable `legacy_surfaces`;
- explicitly proves `docs/agents/programs/FTAI_PORTAL_REMEDIATION_PROGRAM.md` is included;
- unions classified text surfaces with the complete Portal documentation scan, so new/unclassified Portal documents still fail closed;
- applies the existing normalized authority-claim vocabulary to that union;
- preserves the bounded allowlist so classified external roll-ups cannot claim current implementation authority.

## Owned paths

- `tests/ci/test_portal_status_authority.py`
- this task record

## Acceptance state

- classified text status surfaces drive prose discovery: **PASS by direct code inspection**;
- classified surfaces outside `docs/ai_platform/portal/` are included: **PASS by direct code inspection**;
- complete Portal docs discovery is preserved: **PASS by direct code inspection**;
- agent task records remain excluded unless explicitly classified: **PASS by construction**;
- immutable #1101 snapshot unchanged: **PASS**;
- PAPER/LIVE structured authority grants unchanged: **PASS**;
- synchronization with current `develop@0bc9fd995a63fac469fa4f014195f5cc83983dec`: **PASS**, merge-forward candidate `07284a3c1846327da58817cf4a56cf7429d2e965` before this checkpoint-only commit;
- runtime/browser E2E: **NOT_APPLICABLE**, documentation/CI governance only;
- required exact-head CI: **WAITING** — on the last observation of `07284a3...`, zizmor and CodeQL were successful while Freqtrade CI and Risk-aware component CI remained queued;
- `tmp-do-not-use` cleanup: **WAITING** — exact single-purpose cleanup workflow run `31676650665` on temporary branch `tmp-cleanup-20260813` is queued; both target and cleanup branches still existed at the last allowed observation;
- fresh independent post-repair audit: **WAITING / REQUIRED**;
- merge: **NOT AUTHORIZED until remaining gates pass**.

## Safety

Documentation/CI governance only. No runtime, deployment, credentials, exchange orders, withdrawals, protected-environment mutation, LIVE transition, or owner-funded Codex/OpenAI/paid-AI use is authorized or used.

## Context checkpoint

```yaml
checkpoint_version: 2
checkpoint_head: LIVE_BRANCH_HEAD_REQUIRED
pre_checkpoint_head: 07284a3c1846327da58817cf4a56cf7429d2e965
repair_commit: 17b2366779c862093e75478a3ea05d02fef4bf68
integrated_develop: 0bc9fd995a63fac469fa4f014195f5cc83983dec
branch: feat/paper-g0-status-authority-20260810
pr: 1449
status: waiting
proven:
  - G0-AUTH-20260813-01 is repaired in the CI guard
  - current-authority prose discovery now covers machine-classified external text surfaces and the complete Portal docs tree
  - branch was merge-forwarded without force to develop@0bc9fd9
  - runtime/browser E2E is not applicable to this documentation/CI-only package
waiting_on:
  - terminal required exact-head Freqtrade CI and Risk-aware component CI after the GitHub Actions queue advances
  - successful exact deletion of tmp-do-not-use by queued cleanup run 31676650665 and self-deletion of tmp-cleanup-20260813
  - genuinely fresh independent post-repair audit with independent context
blockers:
  - no permitted independent fresh validator is exposed in the current execution surface; owner-funded Codex/OpenAI/paid-AI is prohibited without separate explicit authorization
next_action: In a fresh invocation, resolve the live PR head, verify exact-head CI and cleanup-branch terminal state after the queue advances, then obtain a permitted genuinely fresh independent audit; merge only if all gates pass and review/base hygiene remains clean.
```
