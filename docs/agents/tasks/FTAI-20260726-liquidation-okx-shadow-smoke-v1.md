---
task_id: FTAI-20260726-liquidation-okx-shadow-smoke-v1
status: ready
branch: feat/liquidation-okx-shadow-smoke-v1
base_branch: develop
created: 2026-07-26
updated: 2026-07-26
related_pr: "#386"
owned_paths:
  - ai_platform/research/liquidations/okx-liquidation-shadow-smoke-policy-v1.json
  - ai_platform/scripts/liquidation_okx_shadow_smoke.py
  - tests/ai_platform_integration/test_liquidation_okx_shadow_smoke.py
  - .github/workflows/ai-platform-okx-liquidation-shadow-smoke.yml
  - docs/ai_platform/LIQUIDATION_OKX_SHADOW_SMOKE.md
  - docs/agents/tasks/FTAI-20260726-liquidation-okx-shadow-smoke-v1.md
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/ai_platform/LIQUIDATION_OKX_SHADOW_SOURCE.md
  - docs/ai_platform/LIQUIDATION_MULTI_SOURCE.md
search_first:
  - current develop and open liquidation ownership
  - current official OKX public liquidation, time and instrument contracts
optional_reads: []
---

# OKX liquidation shadow smoke v1

## Goal

Freeze the public, credential-free OKX transport smoke and deterministic artifact evaluator before executing a
separate exact-one-file trigger. Keep OKX outside `liquid20-v1`, LQ-02, replay, models and trading.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-26T19:25:00Z
head: 72b6189c02d717b38806fc05c94c74172f068f0e
branch: feat/liquidation-okx-shadow-smoke-v1
pr: "#386"
status: ready
context_routes:
  - docs/ai_platform/LIQUIDATION_OKX_SHADOW_SOURCE.md
  - docs/ai_platform/LIQUIDATION_OKX_SHADOW_SMOKE.md
  - docs/agents/tasks/FTAI-20260726-liquidation-okx-shadow-source-v1.md
owned_paths:
  - ai_platform/research/liquidations/okx-liquidation-shadow-smoke-policy-v1.json
  - ai_platform/scripts/liquidation_okx_shadow_smoke.py
  - tests/ai_platform_integration/test_liquidation_okx_shadow_smoke.py
  - .github/workflows/ai-platform-okx-liquidation-shadow-smoke.yml
  - docs/ai_platform/LIQUIDATION_OKX_SHADOW_SMOKE.md
  - docs/agents/tasks/FTAI-20260726-liquidation-okx-shadow-smoke-v1.md
proven:
  - PR 339 merged as 11ad81870c0b199b0739af9dcfa239cb32d455cc.
  - OKX remains shadow_only_not_in_liquid20_v1.
  - The six-file prospective smoke package is published in PR 386 at 72b6189c02d717b38806fc05c94c74172f068f0e.
  - The collector uses public endpoints, refuses recognized trading credentials and freezes instrument metadata.
  - The policy permits zero liquidation events in the short transport smoke while requiring public control traffic, clock probes and exact artifact integrity.
  - Temporary diagnostics are absent from the final PR diff and the numeric JSON helpers were narrowed without type ignores.
  - Exact head 72b6189c02d717b38806fc05c94c74172f068f0e passed AI Platform CI 1683, Freqtrade CI 2031 and zizmor 1894.
derived:
  - The next safe liquidation action is the separate exact-one-file public smoke trigger.
  - A separate prospective long-run acceptance policy is required after transport compatibility is proven.
  - A passing smoke cannot unblock LQ-02 or authorize performance research.
unknown:
  - Whether the public OKX endpoints are reachable from the GitHub-hosted Ubuntu runner.
  - Whether the two-minute window will contain liquidation events.
  - Exact operational metrics until the separate trigger reaches a terminal state.
conflicts: []
first_failure:
  marker: smoke-not-yet-executed
  evidence: The prospective infrastructure is ready, but the exact-one-file operational trigger has not run.
rejected_hypotheses:
  - Add OKX directly to liquid20-v1.
  - Require a liquidation event during a two-minute transport smoke.
  - Run the smoke from an infrastructure PR before its policy is merged.
  - Suppress mypy findings instead of narrowing accepted JSON scalar types.
  - Treat smoke success as performance or trading authorization.
changed_paths:
  - ai_platform/research/liquidations/okx-liquidation-shadow-smoke-policy-v1.json
  - ai_platform/scripts/liquidation_okx_shadow_smoke.py
  - tests/ai_platform_integration/test_liquidation_okx_shadow_smoke.py
  - .github/workflows/ai-platform-okx-liquidation-shadow-smoke.yml
  - docs/ai_platform/LIQUIDATION_OKX_SHADOW_SMOKE.md
  - docs/agents/tasks/FTAI-20260726-liquidation-okx-shadow-smoke-v1.md
validation:
  - command: AI Platform CI
    result: PASS
    evidence: Run 30216189643 passed compile, all AI tests, Ruff, Ruff format, codespell and JSON validation on exact head 72b6189c02d717b38806fc05c94c74172f068f0e.
  - command: Freqtrade CI
    result: PASS
    evidence: Run 30216189639 passed pre-commit including mypy, documentation, Linux Python 3.11 through 3.14, coverage, package build and CI Gate on exact head 72b6189c02d717b38806fc05c94c74172f068f0e.
  - command: GitHub Actions Security Analysis with zizmor
    result: PASS
    evidence: Run 30216189628 passed on exact head 72b6189c02d717b38806fc05c94c74172f068f0e.
blockers: []
next_action: Merge PR 386, then open a separate exact-one-file trigger PR and close it without merge after terminal smoke evidence is captured.
```
