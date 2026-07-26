---
task_id: FTAI-20260726-liquidation-okx-shadow-smoke-v1
status: validating
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
updated_at: 2026-07-26T19:07:00Z
head: 16be62197773db288d7d9fc8770374ab0a8ac130
branch: feat/liquidation-okx-shadow-smoke-v1
pr: "#386"
status: validating
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
  - Infrastructure and mypy repair are published in PR 386 at 16be62197773db288d7d9fc8770374ab0a8ac130.
  - The merged collector uses public endpoints, refuses recognized trading credentials and freezes instrument metadata.
  - Official OKX contracts still expose the public WebSocket, public time and public SWAP instrument metadata used by the collector.
  - AI Platform CI 1669 passed compile, all AI tests, Ruff, Ruff format, codespell and JSON validation on code head c53601d5399118f6398b7c2928e8d43163d2085c.
  - Zizmor 1880 passed the production workflow on code head c53601d5399118f6398b7c2928e8d43163d2085c.
  - Two pre-commit mypy findings were narrowed without ignores, and both temporary diagnostic workflows are absent from the six-file PR diff.
derived:
  - The next safe liquidation package is a short transport smoke with zero event minimum.
  - A separate prospective long-run acceptance policy is required after transport compatibility is proven.
  - A passing smoke cannot unblock LQ-02 or authorize performance research.
unknown:
  - Whether the public OKX endpoints are reachable from the GitHub-hosted Ubuntu runner.
  - Whether the two-minute window will contain liquidation events.
  - Exact operational metrics until the separate trigger reaches a terminal state.
conflicts: []
first_failure:
  marker: smoke-not-yet-executed
  evidence: The infrastructure and prospective gates must merge before the exact-one-file trigger is opened.
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
    evidence: Run 30215867040 passed compile, all AI tests, Ruff, Ruff format, codespell and JSON validation on c53601d5399118f6398b7c2928e8d43163d2085c.
  - command: GitHub Actions Security Analysis with zizmor
    result: PASS
    evidence: Run 30215867061 passed on c53601d5399118f6398b7c2928e8d43163d2085c.
  - command: pre-commit diagnostic before mypy repair
    result: FAIL
    evidence: Artifact 8635823799 isolated exactly two numeric input narrowing errors; all other hooks passed and the errors were fixed at 16be62197773db288d7d9fc8770374ab0a8ac130.
  - command: repository CI on exact current PR head
    result: NOT_RUN
    evidence: Run after this checkpoint update triggers exact-head workflows.
blockers: []
next_action: Merge the prospective smoke infrastructure after exact-head CI, then open a separate exact-one-file trigger PR and close it without merge after terminal evidence is captured.
```
