---
task_id: FTAI-20260724-liquidation-symbol-universe-v1
status: validating
branch: feat/liquidation-symbol-universe-v1
base_branch: develop
created: 2026-07-24
updated: 2026-07-24
related_pr: "#254"
owned_paths:
  - ai_platform/research/liquidations/symbol-universes-v1.json
  - ai_platform/research/liquidations/symbol_universe.py
  - ai_platform/research/liquidations/evidence/liquid20-subscription-github-us-20260724-v1.json
  - ai_platform/scripts/liquidation_multi_source_runner.py
  - tests/ai_platform_integration/test_liquidation_symbol_universe.py
  - docs/ai_platform/LIQUIDATION_MULTI_SOURCE.md
  - docs/agents/tasks/FTAI-20260724-liquidation-symbol-universe-v1.md
required_reads:
  - AGENTS.md
  - docs/ai_platform/ARCHITECTURE.md
  - docs/ai_platform/ROADMAP.md
  - docs/ai_platform/LIQUIDATION_MULTI_SOURCE.md
---

# Liquidation Symbol Universe v1

## Goal

Expand multi-source liquidation collection from BTCUSDT and ETHUSDT to a frozen, auditable 20-symbol universe shared by Bybit linear and Binance USD-M, without changing source semantics, enabling execution, or claiming operational acceptance.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-24T13:25:00Z
head: 598fc3285268d0856427005ced9cebec1abda774
branch: feat/liquidation-symbol-universe-v1
pr: "#254"
status: validating
context_routes:
  - docs/ai_platform/LIQUIDATION_MULTI_SOURCE.md
owned_paths:
  - ai_platform/research/liquidations/symbol-universes-v1.json
  - ai_platform/research/liquidations/symbol_universe.py
  - ai_platform/research/liquidations/evidence/liquid20-subscription-github-us-20260724-v1.json
  - ai_platform/scripts/liquidation_multi_source_runner.py
  - tests/ai_platform_integration/test_liquidation_symbol_universe.py
  - docs/ai_platform/LIQUIDATION_MULTI_SOURCE.md
  - docs/agents/tasks/FTAI-20260724-liquidation-symbol-universe-v1.md
proven:
  - PR #250 and checkpoint PR #253 are merged on develop, providing separate Bybit and Binance collectors.
  - Both existing collectors accept arbitrary repeated symbols and preserve per-source files and summaries.
  - The branch defines frozen profile liquid20-v1 with 20 exact uppercase USDT perpetual symbols.
  - The loader rejects duplicates, count mismatches, invalid symbols, unknown profiles, inconsistent thresholds, and profiles above the hard maximum of 100.
  - Profiles above 50 symbols require the explicit --allow-broad-universe capacity acknowledgement.
  - The multi-source runner supplies the identical frozen profile to both collectors, refuses trading credentials, and records separate outputs plus a combined manifest.
  - Focused tests, compile, and Ruff check passed before the final formatting-only correction.
  - GitHub Actions run 30089322467 job 89468775700 received successful production public-WebSocket subscription acknowledgements from Bybit linear and Binance USD-M for the complete 20-symbol profile.
  - Machine-readable subscription evidence is preserved at ai_platform/research/liquidations/evidence/liquid20-subscription-github-us-20260724-v1.json.
derived:
  - Twenty symbols are operationally small for both public connections and materially increase the chance of observing liquidation events relative to BTC and ETH alone.
  - A frozen profile is reproducible, unlike a continuously changing market-cap or 24-hour-volume ranking.
  - A 100-symbol profile is technically permitted by the loader but should remain a separate capacity and symbol-lifecycle work package.
unknown:
  - Final repository CI result for the clean evidence and checkpoint head.
  - Per-symbol liquidation frequency, 24-hour availability, storage growth, and source-specific gaps for liquid20-v1.
conflicts: []
first_failure:
  marker: none
  evidence: All functional and subscription validations completed so far passed; only final repository CI remains.
rejected_hypotheses:
  - Call an unstable market-cap ranking top 20 without freezing its identity.
  - Start with 100 symbols before measuring event volume, symbol churn, storage, and parser health on 20.
  - Merge cross-exchange events or remove source labels.
  - Treat successful subscription acknowledgement as 24-hour operational acceptance or profitability evidence.
changed_paths:
  - ai_platform/research/liquidations/symbol-universes-v1.json
  - ai_platform/research/liquidations/symbol_universe.py
  - ai_platform/research/liquidations/evidence/liquid20-subscription-github-us-20260724-v1.json
  - ai_platform/scripts/liquidation_multi_source_runner.py
  - tests/ai_platform_integration/test_liquidation_symbol_universe.py
  - docs/ai_platform/LIQUIDATION_MULTI_SOURCE.md
  - docs/agents/tasks/FTAI-20260724-liquidation-symbol-universe-v1.md
validation:
  - command: focused AI Platform tests
    result: PASS
    evidence: Profile loading, validation, broad-universe gating, and immutable-target checks passed in repository CI.
  - command: Ruff check
    result: PASS
    evidence: Run 30089026845 completed successfully after the branch-local refactor.
  - command: liquid20 production subscription smoke
    result: PASS
    evidence: Run 30089322467 job 89468775700 accepted the full 20-symbol subscription set on both public sources.
blockers:
  - Final clean-head repository CI has not completed.
  - No 24-hour multi-source operational run exists for liquid20-v1 on the intended non-restricted staging host.
next_action: Complete final clean-head CI, merge PR #254, then declare and run a 24-hour liquid20-v1 multi-source acceptance package on the intended staging host.
```
