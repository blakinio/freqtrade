---
task_id: FTAI-20260725-portal-liquidations-read-model
status: implementing
branch: feat/portal-liquidations-read-model-20260725
base_branch: develop
created: 2026-07-25
updated: 2026-07-25
related_pr: ""
owned_paths:
  - ai_platform/portal/web/lib/liquidations/
  - ai_platform/portal/web/fixtures/liquidations/
  - ai_platform/portal/web/e2e/liquidation-read-model.spec.ts
  - docs/ai_platform/portal/DATA_AND_OBSERVABILITY_ARCHITECTURE.md
  - docs/agents/tasks/FTAI-20260725-portal-liquidations-read-model.md
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/programs/FTAI_AI_TRADING_PORTAL_PROGRAM.md
  - docs/ai_platform/portal/README.md
  - docs/ai_platform/portal/SYSTEM_ARCHITECTURE.md
  - docs/ai_platform/portal/SECURITY_ARCHITECTURE.md
  - docs/ai_platform/portal/DATA_AND_OBSERVABILITY_ARCHITECTURE.md
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
updated_at: 2026-07-25T22:05:00Z
head: 48b894017aef517e1be2cd944bc05538d3c4e94d
branch: feat/portal-liquidations-read-model-20260725
pr: none
status: implementing
context_routes:
  - docs/agents/programs/FTAI_AI_TRADING_PORTAL_PROGRAM.md
  - docs/ai_platform/portal/DATA_AND_OBSERVABILITY_ARCHITECTURE.md
  - docs/ai_platform/LIQUIDATION_MULTI_SOURCE.md
owned_paths:
  - ai_platform/portal/web/lib/liquidations/
  - ai_platform/portal/web/fixtures/liquidations/
  - ai_platform/portal/web/e2e/liquidation-read-model.spec.ts
  - docs/ai_platform/portal/DATA_AND_OBSERVABILITY_ARCHITECTURE.md
  - docs/agents/tasks/FTAI-20260725-portal-liquidations-read-model.md
proven:
  - develop head 48b894017aef517e1be2cd944bc05538d3c4e94d includes the private Synology portal preview on port 3031.
  - Liquid20 collector run liquid20-20260725T212201Z-1 is active on Synology with immutable image c00a091c5adc67cf75c46db5805e358ffc72fad7.
  - The previous complete 24-hour run failed only binance-usdm.maximum_latency_over_threshold_ratio under the unchanged frozen acceptance policy.
  - The portal deployment currently runs the Next.js application in explicit fixture mode and does not deploy the Python control plane.
  - A Next.js server-only bounded reader is the smallest deployable architecture that preserves the browser-to-BFF boundary.
derived:
  - The first package must not own navigation, page UI or deployment paths; those remain separate PRs.
  - The read-model must expose source-labelled aggregates and must never deduplicate events across exchanges.
unknown:
  - Exact final acceptance result of the currently active 24-hour retry.
conflicts: []
first_failure:
  marker: PROMPT_PR_PRECOMMIT
  evidence: Prompt PR 304 documentation build and zizmor passed, while Freqtrade CI pre-commit failed; implementation does not depend on merging that documentation-only PR.
rejected_hypotheses:
  - Expose Liquid20 files, collector, Freqtrade REST or WebSocket directly to the browser.
  - Add a new microservice or Docker socket mount for the first read-only package.
  - Relax or reinterpret the frozen Liquid20 acceptance policy.
changed_paths:
  - docs/agents/tasks/FTAI-20260725-portal-liquidations-read-model.md
validation:
  - command: live-state preflight
    result: PASS
    evidence: Repository heads, open PRs, issue 148, portal deployment, collector state and ownership were checked before declaration.
blockers: []
next_action: Implement the versioned bounded Liquid20 reader and focused Playwright-runner contract tests on this branch.
```
