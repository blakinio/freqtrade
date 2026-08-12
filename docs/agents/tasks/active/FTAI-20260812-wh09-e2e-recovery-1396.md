---
task_id: FTAI-20260812-wh09-e2e-recovery-1396
status: waiting
programme: wickhunter-wh09
related_issue: 1396
branch: codex/wh09-e2e-recovery-closeout-1396
base_head: 584538e9867d38a17b3b1a27f7b9cce452af318a
owner: codex
paper_only: true
next_action: Observe canonical Liquid20 deployment run 31596389251 after its terminal result, then verify sustained producer and downstream PAPER evidence.
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
updated_at: 2026-08-12T12:27:00Z
head: c0c484a1fe9139e6039e0c79512c3b0527c32446
branch: codex/wh09-e2e-recovery-closeout-1396
pr: 1502 merged; closeout PR pending
status: waiting
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
  - PR 1502 merged as c0c484a1fe9139e6039e0c79512c3b0527c32446 after exact-head CI passed and fresh Codex review found no major issues.
  - Both P2 review findings were repaired and their threads resolved before merge.
  - Canonical Liquid20 deployment run 31596389251 started for the exact merge commit.
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
  - command: PR 1502 exact-head required CI
    result: PASS
    evidence: Freqtrade CI, AI Platform component, CodeQL and zizmor gates passed for 3614e4caf65fa01d3366bad225a5feef8adf1862.
  - command: fresh Codex review of 3614e4caf65fa01d3366bad225a5feef8adf1862
    result: PASS
    evidence: no major issues; two earlier P2 findings were fixed and resolved.
blockers: []
next_action: observe canonical Liquid20 deployment run 31596389251 after its terminal result, then verify sustained producer and downstream PAPER evidence
```

## Recovery checkpoint

```yaml
recovery:
  policy_version: 1
  generation: 2
  session_id: 20260812T120700Z-wh09-recovery-1396
  session_started_at: 2026-08-12T12:07:00Z
  checkpointed_at: 2026-08-12T12:27:00Z
  last_progress_at: 2026-08-12T12:25:48Z
  phase: canonical-liquid20-deployment
  exact_head: c0c484a1fe9139e6039e0c79512c3b0527c32446
  pull_request: 1502 merged
  active_operation: Liquidations Live Synology workflow
  external_run_ids:
    - 31596389251
  operation_started_at: 2026-08-12T12:25:48Z
  wait_deadline_at: 2026-08-12T13:10:48Z
  check_generation: liquid20-deploy-c0c484a1fe9139e6039e0c79512c3b0527c32446
  checks_used: 0
  status: waiting
  safe_to_resume: true
  resume_condition: workflow run 31596389251 reaches a terminal conclusion
  next_action: observe run 31596389251 once after the bounded deployment window or on terminal completion
```
