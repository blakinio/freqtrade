---
task_id: FTAI-20260725-portal-liquidations-read-model
status: done
branch: develop
base_branch: develop
created: 2026-07-25
updated: 2026-07-26
related_pr: "#307"
owned_paths:
  - ai_platform/portal/web/lib/liquidations/
  - ai_platform/portal/web/fixtures/liquidations/
  - ai_platform/portal/web/e2e/liquidation-read-model.spec.ts
  - docs/ai_platform/portal/LIQUIDATIONS_READ_MODEL.md
  - docs/agents/tasks/FTAI-20260725-portal-liquidations-read-model.md
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/programs/FTAI_AI_TRADING_PORTAL_PROGRAM.md
  - docs/ai_platform/portal/LIQUIDATIONS_AND_AI_BOT_ARCHITECTURE.md
  - docs/ai_platform/portal/LIQUIDATIONS_READ_MODEL.md
search_first:
  - open portal, Liquid20 and Synology pull requests
  - active task ownership for portal web and deployment paths
optional_reads:
  - docs/ai_platform/LIQUIDATION_MULTI_SOURCE.md
---

# Portal Liquidations read-model

## Goal

Deliver the smallest complete versioned, bounded and read-only server-side read-model for Liquid20 event, summary and health data without changing collector evidence, acceptance policy, portal UI, deployment, execution authority or live-capital boundaries.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-26T07:04:00Z
head: aa2f193b970588e478b5d57f58d2ddfd7f4aab67
branch: develop
pr: "#307"
status: done
context_routes:
  - docs/ai_platform/portal/LIQUIDATIONS_AND_AI_BOT_ARCHITECTURE.md
  - docs/ai_platform/portal/LIQUIDATIONS_READ_MODEL.md
  - docs/ai_platform/LIQUIDATION_MULTI_SOURCE.md
owned_paths:
  - ai_platform/portal/web/lib/liquidations/
  - ai_platform/portal/web/fixtures/liquidations/
  - ai_platform/portal/web/e2e/liquidation-read-model.spec.ts
  - docs/ai_platform/portal/LIQUIDATIONS_READ_MODEL.md
  - docs/agents/tasks/FTAI-20260725-portal-liquidations-read-model.md
proven:
  - PR #307 merged to develop as aa2f193b970588e478b5d57f58d2ddfd7f4aab67.
  - The reader discovers only fixed non-symlinked Liquid20 runs and source files below the configured root.
  - Incremental reads handle partial final lines, file replacement, truncation and run rotation.
  - The cache, request limits, metadata size and NDJSON line size are bounded and truncation is explicit.
  - Ordering and cursor pagination are deterministic.
  - Decimal aggregation remains exact and source-labelled for 5m, 1h and 24h windows.
  - Deduplication is limited to source plus source_event_id; Bybit and Binance are never deduplicated across sources.
  - Health exposes live, stale and historical modes, current acceptance, latest completed acceptance, research_preview true and trading_authorized false.
  - Portal Web CI, Portal Universal E2E, AI Platform CI, Freqtrade CI and zizmor passed on the final PR head.
derived:
  - Browser publication must remain behind a same-origin BFF.
  - Future strategy or AI work must consume a separately frozen dataset and cannot reinterpret portal availability as strategy validation.
unknown: []
conflicts: []
first_failure:
  marker: PROMPT_PR_PRECOMMIT
  evidence: The earlier prompt-only PR initially exposed a documentation pre-commit issue; it did not affect the read-model implementation and was resolved separately.
rejected_hypotheses:
  - Expose Liquid20 files, collector, Freqtrade REST or WebSocket directly to the browser.
  - Add a new microservice or Docker socket mount for the first read-only package.
  - Relax or reinterpret the frozen Liquid20 acceptance policy.
  - Treat source-unlabelled cross-exchange totals as authoritative liquidation volume.
changed_paths:
  - ai_platform/portal/web/lib/liquidations/contracts.ts
  - ai_platform/portal/web/lib/liquidations/decimal.ts
  - ai_platform/portal/web/lib/liquidations/event.ts
  - ai_platform/portal/web/lib/liquidations/index.ts
  - ai_platform/portal/web/lib/liquidations/reader.ts
  - ai_platform/portal/web/fixtures/liquidations/
  - ai_platform/portal/web/e2e/liquidation-read-model.spec.ts
  - docs/ai_platform/portal/LIQUIDATIONS_READ_MODEL.md
  - docs/agents/tasks/FTAI-20260725-portal-liquidations-read-model.md
validation:
  - command: Portal Web CI run 30177413997
    result: PASS
    evidence: TypeScript, lint, production build and portal web tests passed.
  - command: Portal Universal E2E run 30177414016
    result: PASS
    evidence: Universal Chromium portal tests passed.
  - command: AI Platform CI run 30177413992
    result: PASS
    evidence: AI Platform validation passed.
  - command: Freqtrade CI run 30177413983
    result: PASS
    evidence: Repository pre-commit and test gates passed.
  - command: GitHub Actions Security Analysis run 30177413981
    result: PASS
    evidence: Zizmor completed successfully.
blockers: []
next_action: Use docs/ai_platform/portal/LIQUIDATIONS_AND_AI_BOT_ARCHITECTURE.md before declaring any new Liquid20 portal, replay, strategy, AI-model or execution package.
```
