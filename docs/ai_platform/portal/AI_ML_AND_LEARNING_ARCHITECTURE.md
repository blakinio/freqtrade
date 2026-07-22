# AI Trading Portal — AI/ML and Learning Architecture

## 1. Objective

Support AI-assisted trading that can learn from new market data and past trade outcomes while preserving reproducibility, protected evaluation boundaries and deterministic execution risk controls.

The platform must become better at generating and evaluating hypotheses without becoming an unconstrained self-modifying live trader.

## 2. Core authority split

```text
AI model                -> prediction
Strategy                 -> trade candidate
Risk Engine              -> approve/reject/resize within policy
Freqtrade                -> execution and trade lifecycle
Post-Trade Intelligence  -> diagnosis and learning evidence
Training Pipeline        -> new candidate artifacts
Promotion Policy         -> eligibility for production use
```

No model confidence score bypasses risk policy.

## 3. Existing research boundary remains authoritative

The portal integrates with, but does not rewrite, the existing AI Platform lifecycle:

`experiment -> candidate -> validated -> dry-run -> shadow -> live-small -> production -> retired`

Current protected facts remain unchanged by this program:

- frozen `entry_prediction_threshold = 0.006`;
- frozen `exit_prediction_threshold = -0.009`;
- protected prospective final holdout v2 `20260801-20260930`;
- one-shot final holdout v2 evaluation not authorized before `2026-10-01 UTC`;
- completed Phase 6 authoritative `selected_model = null`;
- PyTorch and RL remain separate experimental/evidence tracks unless a future prospectively declared work package changes their status.

Portal features must not expose a button or API that can accidentally violate these boundaries.

## 4. Model identity

Production and candidate models are immutable versioned resources.

```text
ModelVersion
  model_version_id
  model_family
  architecture
  artifact_uri
  artifact_hash
  code_revision
  freqtrade_version
  freqai_identifier
  dataset_version_id
  feature_schema_version
  target_definition_version
  training_pipeline_version
  hyperparameters
  training_window
  validation_contract_id
  metrics_summary
  lifecycle_state
  created_at
```

Changing any identity-defining input creates a new `ModelVersion`.

Never use mutable names such as `production_model.pkl` as identity.

## 5. Dataset and feature identity

### DatasetVersion

```text
DatasetVersion
  dataset_version_id
  source_manifest
  market_universe
  timeframes
  start_time
  end_time
  exclusions
  integrity_hash
  created_at
```

### FeatureSchemaVersion

```text
FeatureSchemaVersion
  feature_schema_version
  feature_names
  feature_definitions
  transformation_versions
  availability_timing
  null_policy
  normalization_policy
  code_revision
```

Feature definitions must state when the information becomes available. Future-derived or post-decision data is forbidden from decision-time features.

## 6. Training architecture

```text
Training Request
      |
      v
Policy / authorization check
      |
      v
Dataset resolver
      |
      v
Feature pipeline
      |
      v
Isolated training job
      |
      +--> LightGBM
      +--> XGBoost
      +--> PyTorch
      +--> RL experimental track
      |
      v
Candidate artifact
      |
      v
Validation pipeline
      |
      v
Model Registry
```

Training workers have no production exchange credentials.

Training jobs are reproducible from pinned inputs and emit machine-readable manifests.

## 7. Validation and promotion

A model candidate does not become production-eligible because its training metric or one backtest improves.

Required policy is lifecycle-dependent and includes the existing AI Platform validation primitives where applicable:

- reproducible experiment inputs;
- out-of-sample evaluation;
- walk-forward evaluation;
- lookahead-analysis;
- recursive-analysis review;
- trade-count and drawdown gates;
- robustness/stability evidence;
- exact model/config identifiers.

Promotion flow:

```text
EXPERIMENTAL
    |
    v
CANDIDATE
    |
    v
VALIDATED
    |
    v
DRY_RUN
    |
    v
SHADOW
    |
    v
LIVE_SMALL   # separate explicit authorization
    |
    v
PRODUCTION
```

Rollback selects a previously immutable approved version; it does not mutate the current artifact.

## 8. Champion / challenger

For recurring model improvement:

```text
Current approved champion
          ^
          |
     fair comparison
          |
New challenger candidate
```

Comparisons use predeclared windows/policies and cannot consume protected final holdouts iteratively.

A challenger may be automatically trained and evaluated. Promotion remains governed by hard gates and the configured approval policy.

## 9. Continual learning loop

Safe continual learning:

```text
Live/dry-run observations
        |
        v
Curated new data
        |
        v
New DatasetVersion
        |
        v
Scheduled/triggered training
        |
        v
Candidate ModelVersion
        |
        v
Validation
        |
        v
Promotion decision
```

Unsafe pattern, explicitly forbidden:

```text
one bad trade -> mutate running model -> redeploy immediately
```

Live evidence can trigger investigation or training, not direct uncontrolled production mutation.

## 10. Decision Black Box

Every AI-assisted trade decision records a reproducible `DecisionSnapshot`.

Minimum fields:

```text
decision_id
correlation_id
tenant_id
bot_id
trade_id if created
occurred_at
strategy_version_id
model_version_id
feature_schema_version
bot_config_revision
risk_policy_version
market_context_ref
feature_vector_ref or bounded snapshot
prediction
prediction_confidence if meaningful
entry_threshold
exit_threshold
do_predict / model eligibility state
strategy_signal
trade_intent
risk_decision
risk_reason_codes
approved_size
```

Large vectors may be stored in object storage with hashes rather than duplicated in PostgreSQL.

This record is the basis for explanation, diagnosis and learning attribution.

## 11. Trade outcome record

On trade lifecycle completion, attach a normalized outcome:

```text
TradeOutcome
  trade_id
  decision_id(s)
  entry_price
  exit_price
  fees
  slippage
  realized_pnl
  duration
  max_favorable_excursion
  max_adverse_excursion
  exit_reason
  execution_anomalies
  market_regime_at_entry
  market_regime_at_exit
```

Loss does not automatically mean the decision was wrong. Outcome quality and decision quality are analyzed separately.

## 12. Post-Trade Intelligence

Post-trade analysis is asynchronous and evidence-based.

```text
Trade closed
    |
    v
Evidence assembler
    |
    v
Deterministic diagnostics
    |
    +--> data quality
    +--> execution quality
    +--> slippage/spread/liquidity
    +--> risk policy behavior
    +--> model eligibility/drift
    +--> regime change
    |
    v
AI-assisted synthesis
    |
    v
TradeAnalysis
```

Suggested diagnosis taxonomy:

```text
GOOD_DECISION_EXPECTED_VARIANCE
BAD_ENTRY_TIMING
BAD_EXIT_TIMING
EARLY_EXIT
LATE_EXIT
MODEL_ERROR_CANDIDATE
RISK_POLICY_ISSUE_CANDIDATE
EXECUTION_ERROR
SLIPPAGE_ANOMALY
LOW_LIQUIDITY
SPREAD_SPIKE
MARKET_REGIME_CHANGE
VOLATILITY_SHOCK
DATA_QUALITY_ERROR
FEATURE_DRIFT
MODEL_DRIFT
UNKNOWN
```

The suffix `CANDIDATE` is intentional where causality is not proven.

## 13. Counterfactual analysis

The intelligence layer may generate offline counterfactual scenarios such as:

- no entry;
- delayed entry;
- earlier/later exit;
- alternate deterministic stop;
- alternate risk sizing;
- threshold perturbation.

Counterfactuals are labeled hypothetical and cannot be presented as causal proof unless the evaluation design supports that claim.

They can create research hypotheses, not direct production edits.

## 14. AI Insights for users

A user-facing insight contains:

```text
Insight
  insight_id
  severity
  affected_bots
  evidence_window
  observation
  evidence_count
  confidence
  hypothesis
  suggested_action
  limitations
  linked_analysis_ids
  status
```

Example intent:

> A cluster of losing entries occurred during volatility regimes underrepresented in the model training set. Consider a bounded experiment evaluating a volatility-regime filter.

The portal must distinguish:

- observation;
- statistical association;
- hypothesis;
- validated finding;
- production recommendation.

## 15. Learning from mistakes and successes

The learning pipeline analyzes both tails:

- poor outcomes and anomalous execution;
- exceptionally good outcomes;
- stable high-quality decisions that lost due to expected variance;
- repeated contexts with model underperformance;
- repeated contexts with model overperformance.

This avoids training the system to overreact to isolated losses.

## 16. Trading Knowledge Base

Validated findings become durable evidence records, not free-form LLM memory.

```text
KnowledgeFinding
  finding_id
  scope
  observation
  evidence_query/version
  evidence_count
  confidence
  validation_status
  created_from_experiments
  supersedes
  created_at
```

LLMs may summarize/query findings. The underlying experiments, metrics and hashes remain the source of truth.

## 17. Autonomy levels

The platform explicitly configures AI autonomy:

```text
L0 observe
L1 analyze
L2 recommend
L3 create bounded experiment proposals
L4 execute authorized training/validation jobs
L5 promote only under predeclared fully automated hard gates
```

Default target for the mature platform: **L4**.

L5 requires a separately reviewed policy and must never imply unrestricted live-capital modification.

## 18. Inference evolution

### Initial

Model inference may remain inside the Freqtrade/FreqAI runtime when that is the simplest supported integration.

### Future

A shared inference service may be introduced for model families that benefit from centralized serving.

Required stable abstraction:

```text
InferenceRequest
  model_version_id
  feature_schema_version
  decision_time
  entity/pair
  features_ref/payload

InferenceResponse
  prediction
  confidence/uncertainty where defined
  model_version_id
  trace_id
```

The execution strategy remains responsible for interpreting predictions under deterministic rules.

## 19. RL-specific boundary

Reinforcement learning remains an experimental research track until separately validated.

Rules:

- no direct online learning with unrestricted live capital;
- training environment and reward definitions are versioned;
- training/inference semantics require explicit parity evidence;
- policy output is still subject to deterministic risk controls;
- RL cannot retroactively enter completed Phase 6 comparison;
- protected/consumed OOS boundaries remain enforced.

## 20. Model health monitoring

Portal AI Health views should expose:

- model age;
- last successful training;
- inference success/rejection counts;
- feature/data drift;
- prediction distribution drift;
- live/dry-run performance divergence from declared expectations;
- stale feature/model conditions;
- analysis backlog;
- active insights;
- current lifecycle state.

Monitoring can trigger alerts or training proposals. It cannot silently rewrite production policy.

## 21. AI/ML invariants

1. Every decision is attributable to immutable versions.
2. Every promoted model has reproducible evidence.
3. Training and deployment are separate actions.
4. Post-trade learning creates evidence/candidates, not immediate self-modification.
5. Protected holdouts are inaccessible to iterative learning loops.
6. Risk policy remains independent from model confidence.
7. LLM-generated explanations never replace machine-readable evidence.
8. Negative results are preserved and cannot be erased to improve perceived model quality.
