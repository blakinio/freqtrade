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
updated_at: 2026-07-26T18:50:00Z
head: 968f1b1c85ab1d86b3854a9941231ec02d250eff
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
  - Infrastructure commit 968f1b1c85ab1d86b3854a9941231ec02d250eff is published in PR 386.
  - The merged collector uses public endpoints, refuses recognized trading credentials and freezes instrument metadata.
  - Official OKX contracts still expose the public WebSocket, public time and public SWAP instrument metadata used by the collector.
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
  - Treat smoke success as performance or trading authorization.
changed_paths:
  - ai_platform/research/liquidations/okx-liquidation-shadow-smoke-policy-v1.json
  - ai_platform/scripts/liquidation_okx_shadow_smoke.py
  - tests/ai_platform_integration/test_liquidation_okx_shadow_smoke.py
  - .github/workflows/ai-platform-okx-liquidation-shadow-smoke.yml
  - docs/ai_platform/LIQUIDATION_OKX_SHADOW_SMOKE.md
  - docs/agents/tasks/FTAI-20260726-liquidation-okx-shadow-smoke-v1.md
validation:
  - command: Python syntax and JSON parsing
    result: PASS
    evidence: The new Python sources parse and the frozen policy is valid JSON before publication.
  - command: repository CI on exact PR head
    result: NOT_RUN
    evidence: Exact-head CI is running on PR 386.
blockers: []
next_action: Merge the prospective smoke infrastructure after exact-head CI, then open a separate exact-one-file trigger PR and close it without merge after terminal evidence is captured.
```
