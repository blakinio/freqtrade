---
task_id: FTAI-20260812-wh09-e2e-recovery-1396
status: validating
programme: wickhunter-wh09
related_issue: 1396
branch: codex/wh09-e2e-recovery-closeout-1396
base_head: c0c484a1fe9139e6039e0c79512c3b0527c32446
owner: chatgpt
paper_only: true
next_action: Complete fresh exact-head CI and independent review for PR 1503, then merge if all gates pass.
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
updated_at: 2026-08-12T15:45:00Z
head: 0e6e41f27ca3dc9da6778753f665b3ee6ec1c0ad
branch: codex/wh09-e2e-recovery-closeout-1396
pr: 1503
status: validating
context_routes:
  - PR 1503 conversation and review threads
  - GitHub Actions exact-head validation for PR 1503
  - canonical Liquidations Live Synology deployment evidence
owned_paths:
  - .github/workflows/liquidations-live-synology.yml
  - deploy/synology/liquid20/deploy-live.sh
  - tests/ai_platform_integration/test_synology_liquid20_live_deployment.py
  - tests/ai_platform_integration/test_liquidation_live_synology_connectivity_diagnostic.py
  - docs/agents/tasks/active/FTAI-20260812-wh09-e2e-recovery-1396.md
proven:
  - PR 1502 merged as c0c484a1fe9139e6039e0c79512c3b0527c32446 after exact-head CI and fresh review passed.
  - Deploy run 31596389251 proved candidate heartbeat advancement and then failed at three-source connectivity readiness.
  - Run 31596389251 discovered Binance 524, Bybit 702 and OKX 431 subscription symbols while all public connected fields remained false.
  - Artifact 9141752696 contains the operational evidence from run 31596389251.
  - Persisted public state cannot identify the private pre-activation source connection set.
  - PR 1503 diagnostic is failure-only, uses the exact built image, passes no credentials or mounts, and preserves fail-closed readiness.
  - Per-source probes are process-isolated with bounded DNS, TLS, WebSocket, protocol and cleanup phases.
  - The diagnostic container has deterministic run identity and ownership labels plus always-run exact-name forced cleanup.
  - GNU timeout uses kill-after so a TERM-resistant docker run is forcibly bounded.
  - Disposable connectivity evidence is uploaded separately with one-day retention.
derived:
  - Accepted diagnostic evidence can distinguish source connection-phase failure without changing PAPER/LIVE authority or readiness semantics.
unknown:
  - The source of the original SIGTERM that produced exit code 143.
  - Which public source or connection phase prevents current atomic three-source activation.
conflicts: []
first_failure:
  marker: canonical deploy run 31596389251 failed at three-source connected readiness
  evidence: heartbeat advanced and subscription discovery completed, but public connected remained false for Binance, Bybit and OKX; artifact 9141752696
rejected_hypotheses:
  - OOM caused exit 143; Docker reported oom_killed false.
  - The post-1502 deploy still fails because candidate heartbeat does not advance.
changed_paths:
  - .github/workflows/liquidations-live-synology.yml
  - tests/ai_platform_integration/test_liquidation_live_synology_connectivity_diagnostic.py
  - docs/agents/tasks/active/FTAI-20260812-wh09-e2e-recovery-1396.md
validation:
  - command: canonical Liquid20 deployment run 31596389251
    result: FAIL
    evidence: heartbeat advanced; readiness failed at three-source connectivity; artifact 9141752696
  - command: GitHub Actions Security Analysis with zizmor on d8802e1671d69898bac9a1b516dec5fd8917c578
    result: PASS
    evidence: run 31612662140 completed successfully
  - command: CodeQL Security Analysis on d8802e1671d69898bac9a1b516dec5fd8917c578
    result: PASS
    evidence: run 31612662138 completed successfully
  - command: exact-head CI and independent review after forced-cleanup and checkpoint-schema repairs
    result: NOT_RUN
    evidence: new exact head is created by this checkpoint update and must be validated before merge
blockers: []
next_action: run checkpoint validation, exact-head CI and fresh independent review for PR 1503, then merge if all gates pass
```

## Recovery checkpoint

```yaml
recovery:
  policy_version: 1
  generation: 6
  session_id: 20260812T131000Z-wh09-recovery-1396
  phase: validate-liquid20-source-connectivity-diagnostic
  pre_checkpoint_code_head: 0e6e41f27ca3dc9da6778753f665b3ee6ec1c0ad
  pull_request: 1503
  external_run_ids:
    - 31596389251
  operational_artifacts:
    - 9141752696
  status: validating
  safe_to_resume: true
  next_action: validate the exact head and merge PR 1503 if CI and independent review pass
```
