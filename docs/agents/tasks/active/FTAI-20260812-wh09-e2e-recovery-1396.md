---
task_id: FTAI-20260812-wh09-e2e-recovery-1396
status: implementing
programme: wickhunter-wh09
related_issue: 1396
branch: codex/wh09-e2e-recovery-closeout-1396
base_head: c0c484a1fe9139e6039e0c79512c3b0527c32446
owner: chatgpt
paper_only: true
next_action: Validate and review the bounded failure-only WebSocket diagnostic on PR 1503, then merge it and collect the next canonical Synology deploy evidence.
---

# WH09 end-to-end production evidence recovery

## Scope

Restore truthful PAPER-only evidence for `Liquid20 -> WickHunter -> Portal API -> Portal UI` after the merged Issue #1396 repair. Do not enable LIVE, credentials, exchange order submission, or any live-capital path.

## Verified entry state

- PR #1487 merged as `584538e9867d38a17b3b1a27f7b9cce452af318a` with required CI green.
- Issue #1396 is reopened because terminal runtime evidence is absent.
- Liquidations Live Health run `31592341447` observed `liquid20-live` exited with code `143`; `oom_killed=false`.
- The exact cause of that SIGTERM / exit `143` remains `UNKNOWN`.
- Deploy run `31540521279` failed before production replacement with `candidate heartbeat did not advance`.
- PR #1502 replaced the fixed candidate-heartbeat sample with bounded monotonic polling and merged as `c0c484a1fe9139e6039e0c79512c3b0527c32446` after exact-head CI and fresh independent review passed.
- Canonical deploy run `31596389251` on that exact merge SHA proved the heartbeat repair worked, then failed at the next readiness gate: candidate `run_state=active`, heartbeat advancing, Binance/Bybit/OKX subscription counts `524/702/431`, but all three public `connected=false`, all output sizes zero, and no public source error (`error_count=0`, `latest_error=null`). Artifact `9141752696` contains the operational evidence.
- Source inspection proves a diagnostic blind spot in `OkxLiveRunManager`: before atomic three-source startup activation, successful individual connections are held in private `_startup_connected_sources`; public `sources[*].connected` remains false until all required sources overlap. The persisted state therefore cannot determine which source reached the pre-activation connected point or which source prevented activation.

## Ownership

Owned paths for the current recovery phase:

- `.github/workflows/liquidations-live-synology.yml`
- `deploy/synology/liquid20/deploy-live.sh`
- `tests/ai_platform_integration/test_synology_liquid20_live_deployment.py`
- `tests/ai_platform_integration/test_liquidation_live_synology_connectivity_diagnostic.py`
- `docs/agents/tasks/active/FTAI-20260812-wh09-e2e-recovery-1396.md`

PR #1503 is the single current recovery PR. No separate runtime implementation PR is being created.

## Acceptance

- bounded monotonic heartbeat advancement validation with explicit timeout;
- enough secret-safe runtime evidence to identify any remaining Liquid20 source-connectivity blocker without weakening readiness;
- focused tests, lint/format and integration validation;
- fresh independent audit and exact-head CI;
- canonical deployment of accepted `develop` revision;
- sustained Binance, Bybit and OKX Liquid20 health;
- natural WickHunter PAPER cycles and production market evidence;
- truthful Portal backend/API/UI E2E;
- Issue #1396 and this record terminal only after all evidence passes.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-08-12T13:24:00Z
head: e0f7323ea5b7256dd726f32a9f4515ac24ba7f6c
branch: codex/wh09-e2e-recovery-closeout-1396
pr: 1503
status: implementing
phase: diagnose-liquid20-source-connectivity
execution_mode: github
execution_reason: authenticated GitHub connector can mutate the owned PR branch and GitHub Actions provides the Synology runner validation path
context_pressure: medium
context_growth: stable
decomposition_decision: phased
owned_paths:
  - .github/workflows/liquidations-live-synology.yml
  - deploy/synology/liquid20/deploy-live.sh
  - tests/ai_platform_integration/test_synology_liquid20_live_deployment.py
  - tests/ai_platform_integration/test_liquidation_live_synology_connectivity_diagnostic.py
  - docs/agents/tasks/active/FTAI-20260812-wh09-e2e-recovery-1396.md
proven:
  - PR 1502 merged as c0c484a1fe9139e6039e0c79512c3b0527c32446 after exact-head CI and fresh Codex review passed.
  - Deploy run 31596389251 no longer failed on candidate heartbeat advancement.
  - Run 31596389251 failed because the candidate did not reach the public three-source connected readiness state.
  - Candidate discovery completed with Binance 524, Bybit 702 and OKX 431 subscription symbols while all public connected fields remained false.
  - Current persisted source state cannot expose the private pre-activation source connection set.
  - Failure-only diagnostic added to PR 1503 uses the exact built image, no credentials or mounts, read-only/cap-drop/no-new-privileges controls, finite DNS/TLS/WebSocket/protocol bounds, sanitized error signatures, and artifact capture.
derived:
  - The next exact-host diagnostic can distinguish DNS, TLS, WebSocket handshake and subscription-protocol failure without changing collector readiness or production state.
unknown:
  - The source of the original SIGTERM that produced exit code 143.
  - Which public source or connection phase prevents current atomic three-source activation.
rejected_hypotheses:
  - OOM caused exit 143; Docker reported oom_killed false.
  - A repository revision change is proven to have stopped the original production container.
  - The post-1502 deploy is still failing because the candidate heartbeat does not advance.
changed_paths:
  - .github/workflows/liquidations-live-synology.yml
  - tests/ai_platform_integration/test_liquidation_live_synology_connectivity_diagnostic.py
  - docs/agents/tasks/active/FTAI-20260812-wh09-e2e-recovery-1396.md
validation:
  - command: canonical Liquid20 deployment run 31596389251
    result: FAIL with new evidence
    evidence: heartbeat advanced; readiness failed at three-source connectivity; artifact 9141752696.
blockers: []
anti_stall:
  invocation_started_at: 2026-08-12T13:10:00Z
  last_progress_at: 2026-08-12T13:24:00Z
  ci_checks_for_current_head: 0
  unchanged_state_checks: 2
  identical_failure_retries: 0
  repair_cycles_for_current_gate: 1
  context_reconstruction_attempts: 1
  stall_warnings: 0
next_action: run focused and exact-head PR validation plus fresh review for the bounded diagnostic, then merge PR 1503 if all gates pass
```

## Recovery checkpoint

```yaml
recovery:
  policy_version: 1
  generation: 3
  session_id: 20260812T131000Z-wh09-recovery-1396
  phase: diagnose-liquid20-source-connectivity
  exact_head: e0f7323ea5b7256dd726f32a9f4515ac24ba7f6c
  pull_request: 1503
  external_run_ids:
    - 31596389251
  operational_artifacts:
    - 9141752696
  status: implementing
  safe_to_resume: true
  next_action: validate and review PR 1503 exact head, then merge to trigger the canonical Liquid20 deployment diagnostic
```
