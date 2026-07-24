---
task_id: FTAI-20260724-liquidation-data-only-staging
status: blocked
branch: develop
base_branch: develop
created: 2026-07-24
updated: 2026-07-24
related_pr: "#247"
owned_paths:
  - ai_platform/research/liquidations/staging.py
  - ai_platform/research/liquidations/data-only-staging-policy-v1.json
  - ai_platform/research/liquidations/evidence/data-only-smoke-github-us-20260724-v1.json
  - ai_platform/scripts/liquidation_collector.py
  - ai_platform/scripts/liquidation_staging_evaluator.py
  - tests/ai_platform_integration/test_liquidation_data_only_staging.py
  - docs/ai_platform/LIQUIDATION_DATA_ONLY_STAGING.md
  - docs/agents/tasks/FTAI-20260724-liquidation-data-only-staging.md
  - docs/agents/tasks/FTAI-20260724-liquidation-reversal-foundation.md
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/ai_platform/ARCHITECTURE.md
  - docs/ai_platform/ROADMAP.md
  - docs/ai_platform/LIQUIDATION_REVERSAL_RESEARCH.md
---

# Liquidation Data-Only Staging

## Goal

Make Stage 1 operationally measurable without loading a Freqtrade strategy, accepting exchange credentials,
submitting orders, enabling DCA, or using the protected final holdout for research.

## Prospective policy

The policy was frozen before live evidence was judged:

- smoke mode: at least 20 seconds, one received message, zero parse failures, synchronized clock, no
  disconnect, new output file, immutable hash, and exact endpoint/symbol contract;
- acceptance mode: at least 24 hours, availability at least `0.995`, no parse failures, at most two
  disconnects per hour, duplicate ratio at most `0.01`, at least ten latency samples, at most `0.01` of
  samples above five seconds, and at least one observed event for each declared symbol;
- both modes require a recorded 40-character Git commit and reject any detected exchange credential
  environment variable;
- smoke success proves transport and evidence generation only; it does not satisfy Stage 1 acceptance.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-24T10:05:00Z
head: b70f4445b7a323f442a2b9b3a7fbdeb3a5d9e764
branch: develop
pr: "#247"
status: blocked
context_routes:
  - docs/ai_platform/ARCHITECTURE.md
  - docs/ai_platform/ROADMAP.md
  - docs/ai_platform/LIQUIDATION_REVERSAL_RESEARCH.md
  - docs/ai_platform/LIQUIDATION_DATA_ONLY_STAGING.md
owned_paths:
  - ai_platform/research/liquidations/staging.py
  - ai_platform/research/liquidations/data-only-staging-policy-v1.json
  - ai_platform/research/liquidations/evidence/data-only-smoke-github-us-20260724-v1.json
  - ai_platform/scripts/liquidation_collector.py
  - ai_platform/scripts/liquidation_staging_evaluator.py
  - tests/ai_platform_integration/test_liquidation_data_only_staging.py
  - docs/ai_platform/LIQUIDATION_DATA_ONLY_STAGING.md
  - docs/agents/tasks/FTAI-20260724-liquidation-data-only-staging.md
  - docs/agents/tasks/FTAI-20260724-liquidation-reversal-foundation.md
proven:
  - Foundation PR #236 merged to develop as 8ab033dd771b3f4695328b22f61c3f6d05a6e1d4.
  - Stage 1 implementation PR #247 merged to develop as b70f4445b7a323f442a2b9b3a7fbdeb3a5d9e764.
  - The merged package provides bounded collection, connection intervals, availability, reconnect, parse, duplicate, symbol, latency, clock, output-hash, and line-count evidence.
  - The frozen policy separates a short transport smoke from a 24-hour operational acceptance run.
  - Nine focused local tests pass.
  - Final AI Platform CI run 30083876114 passed compile, all tests, Ruff, Ruff format, codespell, and JSON validation.
  - Final Freqtrade CI run 30083876126 passed pre-commit, mypy, documentation, coverage, cross-platform core tests, backtesting, Hyperopt, and lint.
  - Final GitHub Actions Security Analysis run 30083876256 passed.
  - GitHub-hosted smoke run 30083558225 connected to the public Bybit linear WebSocket for 29.516 seconds, received the subscription acknowledgement, recorded zero disconnects and zero parse failures, and produced an integrity summary.
  - The smoke failed only the clock_synchronized gate because the Bybit REST clock endpoint returned HTTP 403 from the United States-hosted runner.
  - Clock diagnostic run 30083654093 reproduced HTTPError 403 in 73 ms.
  - The failed smoke is preserved as machine-readable evidence and the policy was not changed after observation.
derived:
  - The collector transport and summary path work on GitHub-hosted infrastructure, but that environment cannot provide authoritative Bybit clock evidence.
  - Bybit documents that United States IP addresses are restricted and receive HTTP 403 for API requests, matching the observed runner behavior.
  - An unchanged smoke must run on the intended non-US staging host before Stage 1 can be accepted.
  - An accepted research interval must remain outside 20260801-20260930 and be frozen separately before replay.
unknown:
  - Smoke result on the intended non-US staging host.
  - Operational 24-hour acceptance evidence from an always-on staging host.
conflicts: []
first_failure:
  marker: bybit-rest-us-403
  evidence: GitHub Actions run 30083654093 returned HTTPError 403 from https://api.bybit.com/v5/market/time while the public WebSocket remained reachable.
rejected_hypotheses:
  - Count a short smoke as Stage 1 acceptance.
  - Weaken or remove the synchronized-clock gate after observing the GitHub-hosted failure.
  - Treat zero liquidations during a short smoke as a transport failure.
  - Store or request exchange API credentials for the public collector.
  - Start a Freqtrade strategy or execution adapter in Stage 1.
changed_paths:
  - ai_platform/research/liquidations/staging.py
  - ai_platform/research/liquidations/data-only-staging-policy-v1.json
  - ai_platform/research/liquidations/evidence/data-only-smoke-github-us-20260724-v1.json
  - ai_platform/scripts/liquidation_collector.py
  - ai_platform/scripts/liquidation_staging_evaluator.py
  - tests/ai_platform_integration/test_liquidation_data_only_staging.py
  - docs/ai_platform/LIQUIDATION_DATA_ONLY_STAGING.md
  - docs/agents/tasks/FTAI-20260724-liquidation-data-only-staging.md
  - docs/agents/tasks/FTAI-20260724-liquidation-reversal-foundation.md
validation:
  - command: PYTHONPATH=. python -m compileall -q ai_platform tests
    result: PASS
    evidence: New and modified Python files compile locally.
  - command: PYTHONPATH=. pytest -q tests/ai_platform_integration/test_liquidation_data_only_staging.py
    result: PASS
    evidence: Nine focused staging, policy, integrity, clock, and deduplication tests passed.
  - command: AI Platform CI run 30083876114
    result: PASS
    evidence: Compile, tests, Ruff, formatting, codespell, and JSON validation passed on the final implementation head.
  - command: Freqtrade CI run 30083876126
    result: PASS
    evidence: Full repository pre-commit, mypy, documentation, coverage, cross-platform tests, and smoke commands passed.
  - command: GitHub Actions Security Analysis run 30083876256
    result: PASS
    evidence: Zizmor completed successfully on the final implementation head.
  - command: Liquidation data-only staging smoke run 30083558225
    result: BLOCKED
    evidence: WebSocket transport passed its observed metrics; only the mandatory clock gate failed.
  - command: Bybit clock diagnostic run 30083654093
    result: BLOCKED
    evidence: The United States-hosted runner received HTTP 403 from the official Bybit REST clock endpoint.
blockers:
  - The unchanged smoke policy has not passed on a non-US staging host.
  - No 24-hour accepted operational run exists yet.
next_action: Run the unchanged smoke and then the 24-hour acceptance mode on the intended non-US always-on staging host.
```
