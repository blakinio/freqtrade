---
task_id: FTAI-20260726-liquidations-lq02-candle-synology-runtime
status: validating
branch: fix/liquid20-candle-synology-runtime
base_branch: develop
created: 2026-07-26
updated: 2026-07-26
related_pr: pending
owned_paths:
  - .github/workflows/ai-platform-liquidation-candle-artifact.yml
  - deploy/synology/liquid20-candle-artifact/Dockerfile
  - deploy/synology/liquid20-candle-artifact/run.sh
  - tests/ai_platform_integration/test_liquidation_candle_synology_runtime.py
  - docs/agents/tasks/FTAI-20260726-liquidations-lq02-candle-synology-runtime.md
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/tasks/FTAI-20260726-liquidations-lq02-candle-artifact.md
  - docs/ai_platform/LIQUIDATION_MULTI_SOURCE.md
  - deploy/synology/portal/README.md
search_first:
  - exact Bybit 403 failure evidence from trigger PR 372
  - current develop and overlapping workflow or Synology runner ownership
  - existing freqtrade-staging runner hardening and deployment evidence
optional_reads: []
---

# LQ-02 Synology candle artifact runtime

## Goal

Move only the reviewed source-separated public candle artifact execution from a US GitHub-hosted runner to the existing Polish Synology staging runner. Preserve the exact request, source identity, atomic output, credential refusal and diagnostic-only boundary.

## Reason

The terminal failure artifact from PR 372 proves that the frozen request reaches `bybit-linear` `BTCUSDT` and receives `HTTP 403 Forbidden` from a GitHub-hosted runner in `eastus`. Bybit's official integration guidance states that US IP addresses are restricted and return 403. The repository already has a proven dedicated `freqtrade-staging` runner on Synology.

## Runtime boundary

The workflow still accepts only the canonical one-file request PR. After that scope check, it builds an exact-commit Python image from a curated context and executes it as numeric non-root with a read-only root filesystem, dropped capabilities, no-new-privileges, PID and memory limits, and no host bind mount. Output remains in an ephemeral Docker volume until all 40 source-symbol files, row counts, identities and SHA-256 entries pass verification. Only then is the evidence copied into the runner workspace for artifact upload.

No exchange credentials are passed into the container. No order, replay, strategy, model, DCA, leverage, protected holdout, portal mutation or live capital is introduced.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-26T14:05:00Z
head: 674d491b0e5a34c873a97c2fe2ff5ce935477250
branch: fix/liquid20-candle-synology-runtime
pr: NOT_OPEN
status: validating
context_routes:
  - docs/agents/tasks/FTAI-20260726-liquidations-lq02-candle-artifact.md
  - docs/ai_platform/LIQUIDATION_MULTI_SOURCE.md
  - deploy/synology/portal/README.md
owned_paths:
  - .github/workflows/ai-platform-liquidation-candle-artifact.yml
  - deploy/synology/liquid20-candle-artifact/Dockerfile
  - deploy/synology/liquid20-candle-artifact/run.sh
  - tests/ai_platform_integration/test_liquidation_candle_synology_runtime.py
  - docs/agents/tasks/FTAI-20260726-liquidations-lq02-candle-synology-runtime.md
proven:
  - Trigger PR 372 passed exact-one-file, checkpoint, credential and frozen-contract gates before public collection.
  - Trigger run 30204742726 failed first at source=bybit-linear symbol=BTCUSDT with HTTP 403 Forbidden.
  - Failure artifact 8632715641 has digest d67320fee5e0430ebca8c4b6e471591223db47ca26d866f5bd5e324f24a15fa6 and records no credentials, orders or partial artifact.
  - Bybit official guidance states that US IP addresses are restricted and return HTTP 403.
  - Runner label freqtrade-staging is proven by successful Synology portal deployment run 30191687921.
  - The Synology runner is containerized and has a working Docker daemon and private-LAN deployment boundary.
derived:
  - Moving the same frozen public request to the existing Polish runner addresses the proven regional blocker without changing source identity.
  - A curated Docker build context avoids exposing the runner checkout or Docker socket to the artifact container.
  - An ephemeral output volume prevents failed or unverified candle files from reaching the uploaded evidence path.
unknown:
  - Whether Bybit and Binance return complete 576-row coverage for every Liquid20 symbol from the Synology public IP.
  - Exact SHA-256 hashes and byte sizes of the eventual 40 candle files.
conflicts: []
first_failure:
  marker: BYBIT_US_RUNNER_HTTP_403
  evidence: PR 372 run 30204742726 failed for bybit-linear BTCUSDT with HTTP 403 before any candle artifact was published.
rejected_hypotheses:
  - Replace Bybit candles with Binance candles.
  - Use an unofficial public proxy or remove source separation.
  - Add credentials to bypass the public endpoint restriction.
  - Publish partial files from the failed GitHub-hosted run.
  - Start replay, strategy, model or execution work before immutable candle evidence exists.
changed_paths:
  - .github/workflows/ai-platform-liquidation-candle-artifact.yml
  - deploy/synology/liquid20-candle-artifact/Dockerfile
  - deploy/synology/liquid20-candle-artifact/run.sh
  - tests/ai_platform_integration/test_liquidation_candle_synology_runtime.py
  - docs/agents/tasks/FTAI-20260726-liquidations-lq02-candle-synology-runtime.md
validation:
  - command: bash -n deploy/synology/liquid20-candle-artifact/run.sh
    result: NOT_RUN
    evidence: Pending exact-head repository CI.
  - command: pytest tests/ai_platform_integration/test_liquidation_candle_synology_runtime.py
    result: NOT_RUN
    evidence: Pending exact-head AI Platform CI.
  - command: zizmor and repository pre-commit
    result: NOT_RUN
    evidence: Pending pull-request checks.
blockers: []
next_action: Open the bounded runtime PR, merge only after exact-head CI is green, then create a new exact-one-file trigger PR and close it without merge after terminal evidence capture.
```
