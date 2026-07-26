# Next-agent prompt: Liquid20 historical backfill and AI training

Copy the prompt below into a fresh agent session. The agent must use repository and live GitHub state as the
source of truth and must not require this chat transcript.

```text
Continue task FTAI-20260726-liquid20-historical-ai-training from repository state.
Do not rely on previous chat history.

REPOSITORY: blakinio/freqtrade
BASE BRANCH: develop
CHECKPOINT:
docs/agents/tasks/FTAI-20260726-liquid20-historical-ai-training.md
PRIMARY ARCHITECTURE:
docs/ai_platform/LIQUID20_HISTORICAL_AI_TRAINING_ARCHITECTURE.md

CROSS-REPOSITORY READ-ONLY CONTEXT:
- blakinio/Oteryn-Platform
- issue 148: Liquid20 Synology status
- deploy/liquid20/README.md
- docs/agents/tasks/active/OTERYN-20260724-liquid20-synology-control.md

MANDATORY READS:
- AGENTS.md
- docs/agents/CONTEXT_HANDOFF.md
- docs/ai_platform/ARCHITECTURE.md
- docs/ai_platform/ROADMAP.md
- docs/ai_platform/LIQUIDATION_REVERSAL_RESEARCH.md
- docs/ai_platform/LIQUIDATION_DATA_ONLY_STAGING.md
- docs/ai_platform/LIQUID20_HISTORICAL_AI_TRAINING_ARCHITECTURE.md
- docs/agents/tasks/FTAI-20260724-liquidation-reversal-foundation.md
- docs/agents/tasks/FTAI-20260724-liquidation-data-only-staging.md
- docs/agents/tasks/FTAI-20260725-portal-liquidations-synology.md

START CONDITION:
- Inspect current develop HEAD, this task checkpoint, active/open PRs, and exact CI state.
- If the declaration containing this prompt is not merged, validate and finish only that declaration first.
- Verify only live state that can invalidate the checkpoint next action; do not repeat broad discovery when the
  checkpoint and repository agree.

CURRENT PROVEN STATE:
- Liquid20 currently collects public Bybit linear and Binance USD-M liquidation data.
- The first immutable 24-hour run completed but failed exactly
  binance-usdm.maximum_latency_over_threshold_ratio.
- The failed run remains immutable; one unchanged retry was started through Oteryn-Platform.
- Do not weaken the frozen live acceptance threshold.
- Portal Liquid20 read-only Synology integration is complete and independent of collector acceptance.
- Phase 6 is complete with selected_model = null.
- PyTorch and RL-v2 are separate evidence tracks and remain unchanged.
- The protected final holdout 20260801-20260930 is forbidden for this work.
- Bybit allLiquidation begins a distinct semantic era on 2025-02-20.
- Tardis is the first event-level historical-provider preflight candidate.
- CoinGlass is an aggregated-data fallback/comparison candidate, not an event-replay substitute.
- OKX is the first later live shadow-source candidate, not part of the first implementation PR.

PRIMARY NEXT ACTION:
Execute H0 — source and historical-provider preflight — on a fresh dedicated branch such as:
feat/liquid20-historical-provider-preflight-v1

H0 OBJECTIVE:
Produce a current, source-backed and machine-readable decision package before implementing an importer or
accessing paid bulk data.

H0 REQUIRED DELIVERABLES:
1. A provider/source preflight document under docs/ai_platform/ that records:
   - exact current official source documentation;
   - event or aggregate semantics;
   - timestamp and publication/arrival semantics;
   - historical date and symbol coverage;
   - known semantic-era boundaries;
   - provider incidents/gaps metadata;
   - licensing and redistribution constraints;
   - authentication and secret requirements;
   - export format, compression, pagination and quotas;
   - expected storage volume and operational cost category;
   - reproducibility and immutable-retention implications.
2. A machine-readable provider decision contract under ai_platform/research/liquidations/historical/ or the
   architecture-declared equivalent.
3. Free-sample inspection evidence where publicly available, with file hashes and no paid credential.
4. An exact recommended first import request for BTCUSDT and ETHUSDT, candidate window
   2025-02-20T00:00:00Z through 2026-07-25T00:00:00Z, adjusted only when verified provider coverage requires a
   narrower declared window.
5. A clear owner-decision list for any subscription, paid download, provider token or material storage cost.
6. Focused schema/JSON/document validation and tests for any executable contract code.
7. An updated compact task checkpoint with exactly one next action.

PREFERRED PROVIDER ORDER:
- Tardis event-level normalized liquidations first.
- CoinGlass aggregated pair liquidation history only as a separate candle-level comparison or fallback.
- Kaiko or another tick vendor only if Tardis coverage, licensing or reproducibility is inadequate.

EXCHANGE POLICY:
- Keep Bybit and Binance as separate feature namespaces.
- Record Bybit legacy and allLiquidation semantic eras separately.
- Record Binance forceOrder snapshot/sampling semantics explicitly.
- Do not create a naive total_exchange_liquidations feature.
- Do not implement OKX, BitMEX, Gate, Deribit, Kraken or CoinEx adapters in H0.
- The H0 document may rank them for later work using current official sources.

NON-NEGOTIABLE BOUNDARIES:
- No bulk paid download or purchase without explicit owner confirmation.
- No provider token, exchange key, secret, raw licensed dataset or model artifact in Git.
- No model training, FreqAI execution, backtest, RL execution or feature selection in H0.
- No current collector, live acceptance policy, Oteryn workflow, Synology evidence, portal or trading change.
- No Phase 5 threshold change.
- No Phase 6 candidate, feature, window, policy, evidence or result change.
- No protected final holdout access.
- No live capital, DCA, leverage optimization, promotion or profitability claim.
- No fabricated events, gaps, arrival timestamps or event IDs.
- Historical provider local timestamps must not be mislabeled as first-party live received_at_ms.

CROSS-REPOSITORY RULE:
Treat blakinio/Oteryn-Platform as read-only during H0. It owns Synology control. Do not modify it from the
Freqtrade task. If later deployment work is required, first finish the Freqtrade exact-SHA implementation and
create a separate Oteryn task that consumes it immutably.

IMPLEMENTATION SEQUENCE AFTER H0:
- Close H0 durably.
- If no owner/provider blocker exists, declare H1 provider-neutral contracts as a separate bounded task and PR.
- Do not combine H0 and H1 changes in one PR.
- Follow the architecture stages H1 through H7, using a separate declaration/infrastructure/execution/evidence
  pattern whenever data access or model execution occurs.

VALIDATION:
- Validate the task checkpoint with:
  python tools/agents/checkpoint.py <task-path> --require-checkpoint
- Run the narrowest relevant tests first.
- Run compile, Ruff, formatting, codespell and JSON validation for changed project files where applicable.
- Use repository CI as authoritative when local dependencies are unavailable.
- Preserve exact file hashes and URLs for inspected free samples.

COMPLETION:
- Open a focused PR against develop.
- Record exact branch, head, PR and CI evidence in the checkpoint.
- Leave exactly one concrete next action.
- Continue autonomously when the next bounded action is safe; stop only for a real provider purchase/license,
  credential, protected-data, or architecture decision requiring the owner.
```
