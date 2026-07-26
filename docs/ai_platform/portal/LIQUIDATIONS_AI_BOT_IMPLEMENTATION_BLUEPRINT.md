# Liquidations AI Bot Implementation Blueprint

Status: **planning and continuation contract**  
Architecture authority: `LIQUIDATIONS_AND_AI_BOT_ARCHITECTURE.md`  
Machine-readable contract: `liquidations-ai-bot-artifact-contracts-v1.json`

## 1. Purpose

This document translates the canonical Liquid20 and AI-bot architecture into a concrete repository layout, artifact contract, package order, test plan, and next-agent workflow.

It does not authorize strategy promotion, order submission, DCA, leverage, or live capital.

## 2. Current implementation boundary

Already implemented and merged:

- canonical liquidation event and deterministic event identity;
- Bybit and Binance source adapters with separate source semantics;
- fixed `liquid20-v1` symbol universe;
- data-only staging and multi-source acceptance policy;
- Synology Liquid20 collector deployment;
- bounded server-side read-model;
- same-origin portal BFF and responsive Liquidations UI;
- read-only Synology evidence mount.

Not implemented or validated:

- accepted research dataset selection;
- deterministic historical replay engine;
- complete candle dataset contract;
- validated deterministic strategy baseline;
- signal-only live observer;
- liquidation-aware AI model;
- dry-run execution adapter for this strategy;
- DCA, selected exits, selected leverage, shadow, or live-small.

## 3. Required repository layout

Future packages should use these project-specific paths unless a live-state preflight proves a better existing boundary.

```text
ai_platform/research/liquidations/
  contracts.py                         # existing canonical event contract
  alignment.py                         # existing conservative candle alignment helper
  signals.py                           # existing pure counter-trade policy foundation
  bybit.py                             # existing Bybit source adapter
  binance.py                           # existing Binance source adapter
  staging.py                           # existing data-only staging evaluation
  multi_source_acceptance.py           # existing multi-source acceptance logic

  datasets/                            # LQ-02
    __init__.py
    contracts.py                       # dataset selection and immutable artifact identities
    selector.py                        # accepted/quarantined interval selection
    hashing.py                         # deterministic file and manifest hashing

  replay/                              # LQ-03
    __init__.py
    contracts.py                       # request, event ordering, fill model, result contracts
    engine.py                          # deterministic event/candle replay
    ordering.py                        # total ordering and tie-breakers
    candles.py                         # versioned candle reader and availability checks
    fills.py                           # delayed entry, fee and slippage model
    evidence.py                        # immutable replay report and artifact hashes

  features/                            # LQ-04/LQ-06
    __init__.py
    contracts.py                       # feature schema and availability policy
    builder.py                         # deterministic baseline features
    liquidation.py                     # source-specific liquidation features
    price_context.py                   # completed-candle VWAP/VWMA/volatility context

  strategies/                          # LQ-04
    __init__.py
    baseline_v1.py                     # pure deterministic baseline
    exits_v1.py                        # only after a separate declared exit package
    sizing_v1.py                       # only after a separate sizing package

  live_observation/                    # LQ-05
    __init__.py
    observer.py                        # signal-only, no order submission
    decision_store.py                  # immutable decisions and rejects
    reconciliation.py                  # replay versus live-timing comparison

  models/                              # LQ-06, optional
    __init__.py
    contracts.py                       # target, feature and artifact identities
    dataset.py                         # training rows from frozen evidence only
    baseline.py                        # required non-AI comparator
    candidate.py                       # optional model candidate implementation
    evaluation.py                      # OOS and trading-metric comparison

  execution/                           # LQ-07, not before gates pass
    __init__.py
    intents.py                         # approved-intent contract only
    adapter.py                         # private dry-run Freqtrade adapter
    reconciliation.py                  # intended versus observed runtime evidence

ai_platform/scripts/
  liquidation_dataset_selector.py      # LQ-02 CLI
  liquidation_replay.py                # LQ-03 CLI
  liquidation_signal_observer.py       # LQ-05 CLI
  liquidation_model_experiment.py      # LQ-06 optional CLI

tests/ai_platform_integration/
  test_liquidation_dataset_selection.py
  test_liquidation_replay.py
  test_liquidation_no_lookahead.py
  test_liquidation_strategy_baseline.py
  test_liquidation_signal_observer.py
  test_liquidation_model_candidate.py
  test_liquidation_dry_run_execution.py

docs/ai_platform/liquidations/
  datasets/
  replays/
  experiments/
  decisions/
```

Do not create all directories in one PR. Each LQ package owns only the paths required for its declared scope.

## 4. Artifact flow

```text
Liquid20 run evidence
  -> DatasetSelectionManifest
  -> ReplayRequest
  -> ReplayEvidenceReport
  -> FeatureArtifact / BaselineDecisionReport
  -> optional ModelCandidateEvidence
  -> SignalObservationReport
  -> approved dry-run IntentEvidence
  -> RuntimeReconciliationReport
```

Every artifact is immutable after completion and references the exact input artifact hashes.

## 5. Mandatory artifact identities

Every completed research or execution artifact must include, when applicable:

```text
schema_version
document_id
created_at
code_commit
dataset_id
input_manifest_hash
collector_commit
parser_contract_version
source_catalog_version
symbol_universe_version
candle_source
candle_artifact_hashes
strategy_version_id
model_version_id or no_model_baseline
feature_schema_version
risk_policy_version_id
bot_config_revision_id
runtime_id
decision_id
correlation_id
```

A display name or mutable path is never sufficient identity.

## 6. LQ-02 accepted dataset selection

### Entry gate

A completed multi-source acceptance report must explicitly contain `passed: true` for performance research.

Failed evidence may be selected only for diagnostics and must remain labelled `diagnostic_only` or `quarantined`.

### Required inputs

- fixed Liquid20 run directory;
- source NDJSON files;
- source summaries;
- multi-source manifest;
- final acceptance report;
- collector, parser, source-catalog, symbol-universe and policy versions;
- versioned candle artifacts covering the requested interval.

### Required output

`DatasetSelectionManifest` containing:

- exact run IDs and file hashes;
- source-specific accepted and quarantined intervals;
- source clock and latency status;
- candle identities and hashes;
- declared allowed purpose;
- train/tune/validation/OOS boundaries when applicable;
- protected-holdout contamination result;
- explicit `performance_research_authorized` boolean.

### Stop conditions

Stop without starting replay when:

- no final report has `passed: true`;
- a required file or hash is missing;
- candle evidence is not versioned;
- source clock or interval integrity cannot be classified;
- requested data overlaps a protected holdout in a prohibited way.

## 7. LQ-03 deterministic replay

The replay request must freeze before execution:

- total event ordering key;
- tie-breakers;
- maximum event age;
- duplicate and conflicting-ID handling;
- candle availability rule;
- entry-price sampling rule;
- decision delay;
- fees;
- slippage;
- missing-event and missing-candle behavior;
- source outage/quarantine behavior;
- warm-up;
- evaluation windows.

### Required ordering

The initial conservative candidate should order by:

```text
received_at_ms
occurred_at_ms
source
source_event_id
```

This is a proposed default, not an approved replay rule. LQ-03 must freeze or replace it prospectively before reading strategy results.

### Required no-lookahead tests

Changing any of the following after an earlier decision point must not change that earlier decision:

- containing-candle final OHLCV;
- later liquidation events;
- later source summaries;
- later acceptance metadata;
- future labels;
- fills and PNL;
- later model outputs.

## 8. LQ-04 deterministic baseline

The first baseline remains a pure function built from:

- canonical liquidation event;
- source freshness and acceptance state;
- allowed source/symbol/direction policy;
- minimum event notional;
- completed-candle VWAP or VWMA context;
- prospectively declared distance thresholds;
- optional prospectively declared volatility or volume filters;
- current position and cooldown state.

Output:

```text
action = enter_long | enter_short | ignore
reason_code
input_evidence_ids
strategy_version_id
```

The first baseline package excludes:

- DCA;
- leverage optimization;
- adaptive exits;
- model prediction;
- order submission.

## 9. LQ-05 signal-only live observation

The observer may consume the live collector stream and candle evidence but must submit no order or approved execution intent.

It persists:

- every accepted or rejected event decision;
- decision-time source and candle evidence;
- reason codes;
- timing from event receipt to decision;
- replay-comparable identities;
- data/source unavailable states.

The package must reconcile live decisions with deterministic replay over the same interval.

## 10. LQ-06 optional AI experiment

AI is added only for one declared question, such as false-reversal filtering or candidate ranking.

Mandatory controls:

- deterministic non-AI baseline;
- frozen dataset and feature schema;
- exact target definition;
- no raw future outcome in decision-time features;
- train/tune/validation/OOS split;
- trading metrics including fees and slippage;
- minimum sample and trade counts;
- repeated-run determinism or declared seed policy;
- negative-result preservation;
- no automatic promotion.

A model cannot create orders or bypass deterministic strategy and risk.

## 11. LQ-07 dry-run execution

Entry dependencies:

- accepted LQ-02 dataset evidence;
- accepted deterministic replay;
- accepted signal-only timing and reconciliation;
- immutable strategy/model/risk/config identities;
- required portal credential and approved-intent contracts.

Initial constraints:

```text
Freqtrade dry_run: true
DCA: false
withdrawals: impossible
strict position cap
strict aggregate exposure cap
daily loss stop
new-entry kill switch
immutable decision and audit evidence
```

No live-small authorization is implied.

## 12. File ownership by package

| Package | Primary owned paths | Forbidden adjacent ownership |
|---|---|---|
| LQ-02 | `datasets/`, dataset selector CLI, dataset tests and evidence docs | replay, models, execution, portal UI |
| LQ-03 | `replay/`, replay CLI and replay/no-lookahead tests | strategy tuning, AI, execution |
| LQ-04 | `features/`, `strategies/baseline_v1.py`, baseline tests | DCA, leverage, adaptive exits, model |
| LQ-05 | `live_observation/`, observer CLI and reconciliation tests | order submission |
| LQ-06 | `models/`, experiment CLI and model tests | promotion, runtime mutation |
| LQ-07 | `execution/`, dry-run adapter and reconciliation tests | live credentials, withdrawals, live capital |

## 13. Validation matrix

| Area | Minimum validation |
|---|---|
| Dataset | JSON/schema validation, deterministic hashes, accepted/quarantined interval tests, holdout check |
| Replay | repeatability, total ordering, no-lookahead mutation tests, gap/outage tests, fee/slippage tests |
| Baseline | pure-function unit tests, reason-code coverage, OOS and walk-forward evidence |
| Live observer | no-order proof, timing evidence, replay reconciliation |
| AI | baseline comparison, leakage checks, OOS trading metrics, repeated seeds where applicable |
| Dry-run | private adapter boundary, risk veto, kill switch, audit, intended/observed reconciliation |
| Repository | checkpoint validation, pre-commit, targeted tests, AI Platform CI, Freqtrade CI, zizmor |

## 14. Agent handoff requirements

Every substantial package must maintain one task checkpoint containing:

- exact branch, head, PR and status;
- proven, derived and unknown facts;
- conflicts and owned paths;
- first failure and rejected hypotheses;
- exact changed paths;
- deterministic validation evidence;
- blockers;
- exactly one concrete `next_action`.

Generate the continuation prompt with:

```bash
python tools/agents/resume.py --task <task-path>
```

## 15. Immediate next legal action

The next agent must not start replay, strategy or model implementation first.

The next bounded package is **LQ-02 accepted dataset selection preflight and contract**:

1. verify current `develop`, open PRs and path ownership;
2. verify the current Synology collector, latest completed runs and final acceptance reports;
3. locate or define versioned candle evidence;
4. declare the dataset-selection contract and stop conditions;
5. implement only the smallest deterministic selector, examples and tests if the entry evidence exists;
6. otherwise record a blocker with exact missing evidence.
