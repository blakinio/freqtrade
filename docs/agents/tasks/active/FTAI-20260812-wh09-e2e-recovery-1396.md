---
task_id: FTAI-20260812-wh09-e2e-recovery-1396
status: validating
programme: wickhunter-wh09
related_issue: 1396
branch: fix/wh09-liquid20-startup-activation-20260812
base_head: 0c450ef7fe29ebbae49e7aea5c051018e3fd28f5
owner: chatgpt
paper_only: true
next_action: Validate exact head of PR 1506, merge when repository gates pass, then prove Liquid20 on the canonical Synology deployment before continuing to WickHunter and Portal evidence.
---

# WH09 end-to-end production evidence recovery

## Scope

Restore truthful PAPER-only evidence for `Liquid20 -> WickHunter -> Portal API -> Portal UI` for Issue #1396. Do not enable LIVE, credentials, exchange order submission, or any live-capital path. Readiness remains fail-closed and all evidence must come from canonical runtime paths rather than synthetic success artifacts.

## Verified history

- PR #1487 merged as `584538e9867d38a17b3b1a27f7b9cce452af318a`; Issue #1396 remained/reopened because terminal runtime evidence was absent.
- Liquidations Live Health run `31592341447` observed `liquid20-live` exited with code `143`; Docker reported `oom_killed=false`. The original SIGTERM source remains `UNKNOWN`.
- PR #1502 fixed candidate-heartbeat validation and merged as `c0c484a1fe9139e6039e0c79512c3b0527c32446`.
- Canonical deploy run `31596389251` proved heartbeat advancement but failed three-source readiness with dynamic subscriptions present and all public source `connected=false`.
- PR #1503 added failure-only, secret-safe connectivity diagnostics and merged as `2456fc375a7f0b785efbf369fcd7a447433a7703`.
- Canonical post-#1503 deploy run `31617078408` failed the same fail-closed readiness gate. Its disposable diagnostic artifact `9150099472` proved DNS, TLS, WebSocket handshake and protocol subscription ACK all succeeded for Binance USDM, Bybit Linear and OKX Swap.
- The same deployment log showed candidate `run_state=active`, advancing collector/source heartbeats, dynamic subscription counts Binance `524`, Bybit `702`, OKX `431`, zero events, no public source error, and all three public `connected=false`.
- Source inspection then isolated the integrated startup barrier: `OkxLiveRunManager.connected()` durably wrote partial pre-activation state while holding the shared async lock even though partial connectivity is intentionally unpublishable. Pre-activation `disconnected()` also removed private startup membership outside that lock.

## Current repair

PR #1506 (`fix/wh09-liquid20-startup-activation-20260812`) is the continuation repair for the same durable task. It:

- keeps partial startup membership private without full durable state writes for the first/second source;
- publishes one durable connected transition only when all three required sources have reached the startup barrier;
- makes pre-activation disconnect membership removal and source failure-state update atomic under the same lock;
- preserves error redaction, reconnect/error accounting, `REQUIRED_LIVE_SOURCES`, and fail-closed semantics;
- adds deterministic regression coverage that runs in the lightweight AI-platform CI environment.

## Ownership

Owned paths for the current recovery phase:

- `ai_platform/scripts/liquidation_live_stream_okx.py`
- `tests/ai_platform/test_liquidation_live_startup_activation.py`
- `.github/workflows/liquidations-live-synology.yml`
- `deploy/synology/liquid20/deploy-live.sh`
- `tests/ai_platform_integration/test_synology_liquid20_live_deployment.py`
- `tests/ai_platform_integration/test_liquidation_live_synology_connectivity_diagnostic.py`
- `docs/agents/tasks/active/FTAI-20260812-wh09-e2e-recovery-1396.md`

The previous statement that PR #1503 was the only recovery PR is superseded: #1503 is merged and its canonical failure evidence is what justified the implementation repair in #1506. No parallel duplicate WH09 recovery task is being created.

## Acceptance

- focused regression tests, lint/format, exact-head repository CI and security gates pass;
- canonical accepted `develop` revision deploys Liquid20 to Synology;
- Binance USDM, Bybit Linear and OKX Swap are simultaneously and sustainably healthy with dynamic subscriptions and natural event flow;
- canonical Liquid20 operational-health evidence passes;
- only after Liquid20 passes, WickHunter research runtime completes natural PAPER cycles and consumes canonical market evidence;
- Portal production backend/API/UI E2E truthfully reflects the resulting PAPER state;
- independent/adversarial audit has no unresolved material finding;
- Issue #1396 and this record become terminal only after the complete evidence chain passes.

## Continuation checkpoint

```yaml
checkpoint_version: 2
updated_at: 2026-08-12T22:44:00Z
branch: fix/wh09-liquid20-startup-activation-20260812
pull_request: 1506
base_head: 0c450ef7fe29ebbae49e7aea5c051018e3fd28f5
pre_checkpoint_head: 29ddf876be8e540fd57a866cac68ed252d9d05c2
status: validating
paper_only: true
owned_paths:
  - ai_platform/scripts/liquidation_live_stream_okx.py
  - tests/ai_platform/test_liquidation_live_startup_activation.py
  - .github/workflows/liquidations-live-synology.yml
  - deploy/synology/liquid20/deploy-live.sh
  - tests/ai_platform_integration/test_synology_liquid20_live_deployment.py
  - tests/ai_platform_integration/test_liquidation_live_synology_connectivity_diagnostic.py
  - docs/agents/tasks/active/FTAI-20260812-wh09-e2e-recovery-1396.md
proven:
  - PR 1503 merged as 2456fc375a7f0b785efbf369fcd7a447433a7703.
  - Canonical deployment 31617078408 failed fail-closed three-source activation on that exact revision.
  - Diagnostic artifact 9150099472 passed DNS, TLS, WebSocket and subscription ACK for Binance USDM, Bybit Linear and OKX Swap.
  - Integrated candidate had active run state, advancing heartbeats and nonzero dynamic subscription counts while all public connected fields remained false.
  - Source-level inspection identified unnecessary partial startup durable writes under the shared manager lock and a pre-activation disconnect race.
  - PR 1506 preserves the three-source atomic readiness requirement and removes those startup-path hazards.
validation:
  - command: CodeQL on PR 1506 head d963f8af56c7fc4794d4e617be9ec940240cae3d
    result: PASS
    evidence: run 31646754693
  - command: zizmor on PR 1506 head d963f8af56c7fc4794d4e617be9ec940240cae3d
    result: PASS
    evidence: run 31646754723
  - command: AI Platform component tests on PR 1506 head d963f8af56c7fc4794d4e617be9ec940240cae3d
    result: TESTS_PASS_LINT_FAIL
    evidence: run 31646754929; regression tests passed before Ruff import-order failure
  - command: pre-commit on PR 1506 head d963f8af56c7fc4794d4e617be9ec940240cae3d
    result: FAIL
    evidence: run 31646754578; only Ruff I001 in the regression-test bootstrap
  - command: exact-head CI after lint-bootstrap repair and this checkpoint update
    result: NOT_RUN
    evidence: this checkpoint commit creates the final validation head
unknown:
  - original source of historical exit 143; OOM is ruled out
  - whether the startup-barrier repair is sufficient in the canonical Synology runtime until post-merge deployment proves it
blockers: []
next_action: allow exact-head PR 1506 gates to complete; merge only if required CI Gate passes; then inspect the canonical push-triggered Liquidations Live Synology deployment and continue through health, WickHunter PAPER runtime, Portal E2E, audit and Issue 1396 closeout
```
