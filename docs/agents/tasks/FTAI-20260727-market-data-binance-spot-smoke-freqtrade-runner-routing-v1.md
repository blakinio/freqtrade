---
task_id: FTAI-20260727-market-data-binance-spot-smoke-freqtrade-runner-routing-v1
status: validating
branch: fix/binance-smoke-freqtrade-runner-routing-v1
base_branch: develop
created: 2026-07-27
updated: 2026-07-27
related_pr: "#522"
owned_paths:
  - .github/workflows/ai-platform-binance-spot-instrument-smoke-selfhosted.yml
  - docs/ai_platform/market_data/BINANCE_SPOT_INSTRUMENT_SMOKE_SELFHOSTED.md
  - tests/ai_platform_integration/test_market_data_binance_spot_instrument_smoke_selfhosted_workflow.py
  - docs/agents/tasks/FTAI-20260727-market-data-binance-spot-smoke-freqtrade-runner-routing-v1.md
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/ai_platform/market_data/BINANCE_SPOT_INSTRUMENT_SMOKE_SELFHOSTED.md
  - .github/workflows/ai-platform-binance-spot-instrument-smoke-selfhosted.yml
search_first:
  - current develop and open Binance Spot smoke, Synology runner and trigger ownership
optional_reads: []
---

# Binance Spot smoke Freqtrade runner routing v1

## Goal

Align the bounded self-hosted Binance Spot smoke with the current repository-owned Synology runner without changing the frozen request, endpoint, retry, evidence or source-acceptance contract.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-27T22:58:00+02:00
head_parent: 961efb5553d5d7199a96ce0c065b39808348f517
base_develop: 351567d57760305b992fb1e441205dc32890dc2a
branch: fix/binance-smoke-freqtrade-runner-routing-v1
pr: "#522"
status: validating
context_routes:
  - docs/ai_platform/market_data/BINANCE_SPOT_INSTRUMENT_SMOKE_SELFHOSTED.md
  - .github/workflows/ai-platform-binance-spot-instrument-smoke-selfhosted.yml
owned_paths:
  - .github/workflows/ai-platform-binance-spot-instrument-smoke-selfhosted.yml
  - docs/ai_platform/market_data/BINANCE_SPOT_INSTRUMENT_SMOKE_SELFHOSTED.md
  - tests/ai_platform_integration/test_market_data_binance_spot_instrument_smoke_selfhosted_workflow.py
  - docs/agents/tasks/FTAI-20260727-market-data-binance-spot-smoke-freqtrade-runner-routing-v1.md
proven:
  - PR 453 merged as 731132c9246a2ae09ee3a2a9c4776ad4f0e4ee6e and corrected the smoke Accept header to application/json.
  - Exact-one-file trigger PR 521 started workflow run 30299645009 but stayed queued before its first step because the merged workflow requested retired oteryn runner labels.
  - PR 521 was closed without merge; no Binance request executed and no payload was collected.
  - Current repository-owned Synology execution uses runner freqtrade-synology-staging with label freqtrade-staging.
  - This repair changes only runner label, exact runner-name assertion, matching documentation and focused static assertions.
  - Protected environment synology-staging, endpoint, one-attempt boundary, zero retries, credential and proxy refusal, evidence handling and source_acceptance false remain unchanged.
  - Exact-head validation passed twice before develop advanced through disjoint task changes, including AI Platform CI 30303995558, Freqtrade CI 30303995614 and zizmor 30303995524 at c5b127d318970c73a98d60e3e686b0cc745cf010.
  - The identical four-path repair is now recreated on develop 351567d57760305b992fb1e441205dc32890dc2a.
derived:
  - The earlier queued result is a repository routing defect, not evidence that the Binance endpoint or parser failed.
  - A fresh exact-one-file trigger is required after this routing repair merges.
unknown:
  - Final exact-head repository CI and review result for the current reconciliation.
  - Whether the current Freqtrade Synology runner is online and available.
  - Terminal result of the fresh bounded Binance Spot request.
conflicts: []
first_failure:
  marker: stale-self-hosted-runner-routing
  evidence: Workflow run 30299645009 requested oteryn-staging and remained queued before all steps while the current repository runner contract is freqtrade-staging.
rejected_hypotheses:
  - Treat the queued job as a Binance HTTP, TLS, parser or schema failure.
  - Change endpoint, add retries, use a proxy or route through another region.
  - Merge a trigger request into develop.
changed_paths:
  - .github/workflows/ai-platform-binance-spot-instrument-smoke-selfhosted.yml
  - docs/ai_platform/market_data/BINANCE_SPOT_INSTRUMENT_SMOKE_SELFHOSTED.md
  - tests/ai_platform_integration/test_market_data_binance_spot_instrument_smoke_selfhosted_workflow.py
  - docs/agents/tasks/FTAI-20260727-market-data-binance-spot-smoke-freqtrade-runner-routing-v1.md
validation:
  - command: prior exact-head repository CI at c5b127d318970c73a98d60e3e686b0cc745cf010
    result: PASS
    evidence: AI Platform CI 30303995558, Freqtrade CI 30303995614 and zizmor 30303995524 succeeded.
  - command: current-develop reconciliation scope
    result: PASS
    evidence: Develop advanced only through disjoint task and deployment paths; the same declared four paths were recreated.
  - command: current exact-head repository CI
    result: PENDING
    evidence: Fresh PR checks must complete before guarded merge.
blockers: []
next_action: Complete fresh exact-head CI and guarded-squash merge PR 522, then create one fresh exact-one-file self-hosted smoke trigger, collect terminal evidence, close the trigger without merge, and record the result while keeping source_acceptance false.
```
