---
task_id: FTAI-20260726-liquidations-lq02-candle-failure-evidence
status: validating
branch: fix/liquid20-candle-failure-evidence
base_branch: develop
created: 2026-07-26
updated: 2026-07-26
related_pr: null
owned_paths:
  - ai_platform/scripts/liquidation_candle_artifact.py
  - .github/workflows/ai-platform-liquidation-candle-artifact.yml
  - tests/ai_platform_integration/test_liquidation_candle_failure_evidence.py
  - docs/agents/tasks/FTAI-20260726-liquidations-lq02-candle-failure-evidence.md
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/tasks/FTAI-20260726-liquidations-lq02-candle-artifact.md
  - ai_platform/research/liquidations/datasets/liquid20-candle-artifact-contract-v1.json
optional_reads: []
---

# LQ-02 candle failure evidence hardening

## Goal

Preserve exact public source and symbol context when diagnostic candle collection fails, and retain bounded non-secret failure evidence without publishing partial candle data.

## Boundaries

No request file is included. No candle download is performed by this package. No replay, model, strategy, credentials, orders, protected holdout or live capital is introduced.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-26T12:27:00Z
head: c23a20026d29286d6e5635f2e6bd816e996e9e3c
branch: fix/liquid20-candle-failure-evidence
pr: NONE
status: validating
context_routes:
  - docs/agents/tasks/FTAI-20260726-liquidations-lq02-candle-artifact.md
  - docs/agents/tasks/FTAI-20260726-liquidations-lq02-dataset-selection.md
owned_paths:
  - ai_platform/scripts/liquidation_candle_artifact.py
  - .github/workflows/ai-platform-liquidation-candle-artifact.yml
  - tests/ai_platform_integration/test_liquidation_candle_failure_evidence.py
  - docs/agents/tasks/FTAI-20260726-liquidations-lq02-candle-failure-evidence.md
proven:
  - PR 350 merged source-separated candle infrastructure as e448c7137e4787525cbba1da2c90a8a98812e219.
  - PR 366 stopped before network access because the checkpoint used unsupported status reviewing.
  - PR 367 repaired the checkpoint and merged as be7b387fa1090ee72b9ba4200f6e71098ed1d2ac.
  - PR 369 passed scope, checkpoint, credential and contract gates but failed during public artifact build.
  - Run 30201875821 published no artifact and preserved no source or symbol in terminal failure evidence.
  - The generator removes partial output atomically on every exception.
derived:
  - A contextual fetch wrapper can identify source and symbol from the already frozen public request URL.
  - Uploading only stderr and explicit safety metadata preserves diagnosis without publishing partial market data.
unknown:
  - Which public endpoint and symbol caused run 30201875821 to fail.
  - Whether the failure is deterministic across GitHub-hosted regions.
conflicts: []
first_failure:
  marker: public-build-failure-without-request-identity
  evidence: Run 30201875821 failed in Build public diagnostic candle artifact after all safety gates passed, while the current exception omitted source and symbol.
rejected_hypotheses:
  - Retry the same trigger without improved evidence.
  - Upload partial candle files after failure.
  - Add credentials or alternate private endpoints.
  - Broaden the request window or access the protected holdout.
changed_paths:
  - ai_platform/scripts/liquidation_candle_artifact.py
  - .github/workflows/ai-platform-liquidation-candle-artifact.yml
  - tests/ai_platform_integration/test_liquidation_candle_failure_evidence.py
  - docs/agents/tasks/FTAI-20260726-liquidations-lq02-candle-failure-evidence.md
validation:
  - command: focused failure-context tests
    result: NOT_RUN
    evidence: Awaiting exact-head repository CI.
  - command: workflow security and syntax validation
    result: NOT_RUN
    evidence: Awaiting exact-head repository CI.
blockers: []
next_action: Open a bounded infrastructure PR, pass exact-head CI, merge it, then open a fresh exact-one-file diagnostic trigger and close that trigger without merge after terminal evidence is captured.
```
