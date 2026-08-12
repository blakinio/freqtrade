---
task_id: FTAI-20260812-wh09-e2e-recovery-1396
status: validating
programme: wickhunter-wh09
related_issue: 1396
branch: codex/wh09-e2e-recovery-1396
base_head: 584538e9867d38a17b3b1a27f7b9cce452af318a
owner: codex
paper_only: true
next_action: Complete fresh audit and exact-head CI for PR 1502, then merge and run the canonical Liquid20 deployment.
---

# WH09 end-to-end production evidence recovery

## Scope

Restore truthful PAPER-only evidence for `Liquid20 -> WickHunter -> Portal API -> Portal UI` after the merged Issue #1396 repair. Do not enable LIVE, credentials, exchange order submission, or any live-capital path.

## Verified entry state

- `develop` and `origin/develop`: `584538e9867d38a17b3b1a27f7b9cce452af318a`.
- PR #1487 merged as that exact commit with required CI green.
- Issue #1396 had been closed but was reopened because terminal runtime evidence is absent.
- Liquidations Live Health run `31592341447` failed: `liquid20-live` is `exited`, exit code `143`, `oom_killed=false`, live-state pointer unavailable; Portal page probe passed but source/runtime health failed.
- WickHunter Production Market Evidence run `31591995194` was skipped while Liquid20 was unavailable.
- Liquid20 deployment run `31540521279` failed before replacement with `candidate heartbeat did not advance`.
- Collector heartbeat cadence is five seconds. Candidate validation took one observation, slept six seconds once, and rejected if the next observation had not advanced. This is a timing race; the smallest repair is bounded polling for a strictly greater heartbeat with a finite timeout and fail-closed diagnostics.
- The cause of the existing production container's SIGTERM / exit `143` remains `UNKNOWN`; repository revision change, OOM, manual stop, and deployment termination are not proven.

## Ownership

Owned paths:

- `deploy/synology/liquid20/deploy-live.sh`
- `tests/ai_platform_integration/test_synology_liquid20_live_deployment.py`
- this task record

No open PR found owning Issue #1396, WH09 recovery, or the Liquid20 deploy paths at task start.

## Acceptance

- bounded monotonic heartbeat advancement validation with explicit timeout;
- focused tests, shell syntax, lint/format and integration validation;
- fresh independent audit and exact-head CI;
- canonical deployment of accepted `develop` revision;
- sustained Binance, Bybit and OKX Liquid20 health;
- natural WickHunter PAPER cycles and production market evidence;
- truthful Portal backend/API/UI E2E;
- Issue #1396 and this record terminal only after all evidence passes.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-08-12T12:12:00Z
head: 192b1a706e35e95bc4829a9961f48fbd0a9bf54b
branch: codex/wh09-e2e-recovery-1396
pr: 1502
status: validating
context_routes:
  - deploy/synology/liquid20/deploy-live.sh
  - tests/ai_platform_integration/test_synology_liquid20_live_deployment.py
owned_paths:
  - deploy/synology/liquid20/deploy-live.sh
  - tests/ai_platform_integration/test_synology_liquid20_live_deployment.py
  - docs/agents/tasks/active/FTAI-20260812-wh09-e2e-recovery-1396.md
proven:
  - develop is 584538e9867d38a17b3b1a27f7b9cce452af318a and PR 1487 is merged.
  - Health run 31592341447 observed liquid20-live exited with code 143 and oom_killed false.
  - Deploy run 31540521279 failed before production replacement because candidate heartbeat did not advance.
  - Collector heartbeat cadence is five seconds and candidate validation used one fixed six-second sample.
derived:
  - Fixed single-sample validation can reject a healthy candidate when scheduling delays straddle the next heartbeat.
unknown:
  - The source of the SIGTERM that produced exit code 143.
conflicts: []
first_failure:
  marker: candidate-heartbeat-fixed-sample
  evidence: Deploy run 31540521279 emitted candidate heartbeat did not advance after fixed-delay validation.
rejected_hypotheses:
  - OOM caused exit 143; Docker reported oom_killed false.
  - A repository revision change is proven to have stopped the container.
changed_paths:
  - deploy/synology/liquid20/deploy-live.sh
  - tests/ai_platform_integration/test_synology_liquid20_live_deployment.py
  - docs/agents/tasks/active/FTAI-20260812-wh09-e2e-recovery-1396.md
validation:
  - command: bash -n deploy/synology/liquid20/deploy-live.sh
    result: PASS
    evidence: local shell syntax validation passed.
  - command: focused deployment pytest excluding Windows-unavailable sh executable check
    result: PASS
    evidence: 10 passed and 1 deselected.
  - command: Ruff check and format check
    result: PASS
    evidence: changed Python test passed lint and formatting checks.
  - command: checkpoint validator and git diff --check
    result: PASS
    evidence: task checkpoint and whitespace validation passed.
blockers: []
next_action: complete fresh audit and exact-head CI for PR 1502, then merge and run the canonical Liquid20 deployment
recovery:
  policy_version: 1
  generation: 1
  session_id: 20260812T121200Z-wh09-recovery-1396
  session_started_at: 2026-08-12T12:07:00Z
  checkpointed_at: 2026-08-12T12:12:00Z
  last_progress_at: 2026-08-12T12:10:35Z
  phase: final-review-and-ci
  exact_head: cfb73d062185b3ea9cccc428840f94f05f5b7dcc
  pull_request: 1502
  active_operation: GitHub Actions exact-head CI and independent review
  external_run_ids:
    - 31595185564
    - 31595185726
  operation_started_at: 2026-08-12T12:10:25Z
  wait_deadline_at: 2026-08-12T12:55:25Z
  check_generation: ready-pr-cfb73d062185b3ea9cccc428840f94f05f5b7dcc
  checks_used: 1
  status: waiting
  safe_to_resume: true
  resume_condition: required CI and an eligible independent review are terminal
  next_action: observe aggregate PR 1502 CI and review state once after the minimum interval
```
