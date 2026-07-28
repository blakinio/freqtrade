# ASE-00 implementation plan

## Objective

Deliver one deterministic, shadow-only AI Strategy Engine vertical slice while preserving the existing repository authority chain:

```text
accepted synthetic market/liquidation data
  -> point-in-time features
  -> declarative Strategy DSL
  -> fail-closed Leakage Guard
  -> existing deterministic Portal Risk Core
  -> immutable shadow evidence
```

No step may call the private Freqtrade runtime or create an order.

## Package ownership

### Strategy research package

Owned paths:

- `ai_strategy_engine/configs/`
- `ai_strategy_engine/schemas/`
- `ai_strategy_engine/examples/`
- `ai_strategy_engine/src/strategy_engine/`
- `ai_strategy_engine/tests/`
- `ai_strategy_engine/docs/`

Responsibilities:

- canonical research contracts;
- registry loading and parameter validation;
- generic clean-room features;
- declarative DSL validation/evaluation;
- point-in-time leakage validation;
- deterministic evidence serialization/hashing;
- research-only Miyagi provenance.

### Existing platform adapter

Owned integration path:

- `ai_platform/research/strategy_engine/ase00_adapter.py`

Focused integration tests:

- `tests/ai_platform_integration/test_ase00_vertical_slice.py`

Responsibilities:

- map accepted synthetic fixtures to ASE feature records;
- invoke the existing algorithm in `ai_platform/portal/risk/service.py` with models from `ai_platform/portal/risk/schema.py`;
- produce shadow evidence only;
- enforce duplicate/out-of-order/restart semantics;
- prevent any dependency on `ai_platform/portal/execution/`.

## Implementation sequence

### 1. Canonical contracts

Extend `ai_strategy_engine/src/strategy_engine/domain/models.py` with immutable extra-forbid models:

- `FeatureRecord`;
- `SignalEvent`;
- `StrategyDefinition`;
- `ValidationReport`;
- `ShadowDecisionEvidence`;
- structured `Provenance`.

Every feature/signal carries schema/version, symbol/timeframe, event/detection/availability timestamps, source, confirmation, idempotency key, code/data/config hashes, and provenance. Canonical JSON and SHA-256 evidence hashes must be deterministic.

Update JSON Schemas and examples in place; do not create competing schema versions for ASE-00.

### 2. Feature Registry loader

Add `ai_strategy_engine/src/strategy_engine/registry.py` to load:

- `configs/feature_registry.v1.yaml`;
- `configs/search_spaces.v1.yaml`.

The loader validates:

- registry version;
- unique feature IDs;
- dependencies and cycles;
- required inputs/sources;
- parameter type/range/enum/default;
- explicit warm-up;
- timestamp and normalization policies;
- `approved_for_ai` and research-only status;
- search-space references and bounds.

### 3. Minimal features

Retain and test:

- `features/squeeze.py`: corrected `bb_mult * stdev`; legacy compatibility only by explicit mode;
- `features/supertrend.py`: direction changes only on closed bars, including gaps;
- `features/pivots.py`: pivot `event_time` at the extremum and `detected_at`/`available_at` after `right_bars` plus optional latency.

Add a small feature-record factory that applies registry timestamp and provenance policy.

### 4. Strategy DSL

Extend `src/strategy_engine/dsl/validator.py` and add `evaluator.py`.

Validation covers:

- `all`, `any`, `none` recursively;
- comparison operators without dynamic code;
- long and short entry sections;
- regime and exit sections;
- risk policy and provenance;
- feature existence and AI approval;
- exact parameter/search-space bounds;
- declared timeframes only;
- closed/confirmed data only.

Evaluation accepts a bounded feature snapshot and returns deterministic action/reason codes. It does not evaluate arbitrary expressions or generated Python.

### 5. Leakage Guard

Extend `src/strategy_engine/validation/leakage.py` with fail-closed reason codes for:

- availability after decision time;
- unconfirmed pivot;
- incomplete HTF bar;
- future shift;
- target leakage;
- unavailable revised data;
- final holdout reuse;
- inconsistent data/code/config versions;
- missing provenance.

Add one negative test per rule.

### 6. Portal Risk Core adapter

Add `ai_platform/research/strategy_engine/ase00_adapter.py`.

The adapter:

- accepts an explicit `AcceptedSyntheticEvent` envelope;
- sorts events by event/detection/availability/idempotency identity;
- ignores exact duplicates;
- rejects conflicting duplicates;
- buffers or rejects out-of-order data according to deterministic watermark rules;
- creates three ASE features: corrected Squeeze, closed-bar Supertrend, confirmed pivot/support-resistance;
- validates the strategy and feature snapshot;
- invokes `RiskService._evaluate` with `RiskPolicyLimits` and `RiskEvaluationSnapshot`;
- writes `ShadowDecisionEvidence` to an atomic JSON file;
- returns the same evidence hash after restart/replay;
- never imports an execution adapter.

### 7. Tests

Unit tests under `ai_strategy_engine/tests/unit/` cover timestamps, Squeeze modes, Supertrend flip/gap, MACD SMA/EMA, pivots, HTF confirmation, cooldown, partial TP, and bounded DCA.

Integration tests under `ai_strategy_engine/tests/integration/` cover registry-to-DSL, feature resolution, leakage, and evidence serialization.

Repository integration/E2E tests under `tests/ai_platform_integration/` cover:

- successful synthetic flow;
- duplicate event;
- delayed event;
- out-of-order event;
- future feature rejection;
- unconfirmed pivot rejection;
- unconfirmed HTF rejection;
- Risk Core rejection;
- restart/replay;
- deterministic evidence hash;
- missing-data fail-closed behavior;
- absence of an execution import/path.

### 8. Validation and checkpoint

Run exactly:

```bash
cd ai_strategy_engine
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest
ruff check .
mypy src/strategy_engine
python -m compileall -q src tests
```

Then run repository integration tests and scans for:

- every JSON file;
- every YAML file;
- JSON Schema examples;
- secrets;
- LuxAlgo code/name boundaries;
- `eval()`/`exec()`;
- Browser-to-Freqtrade references/imports;
- deterministic hashes and replay.

Write exact command/output evidence and checkpoint hashes to:

- `ai_strategy_engine/docs/validation-evidence.md`;
- `ai_strategy_engine/docs/IMPLEMENTATION_CHECKPOINT.md`.

Update draft PR #584, preserve draft status, and do not merge.

## Rollback

Rollback is a normal revert of ASE-00 commits. The package has no migration, live order, exchange credential, Freqtrade API, or capital path. The existing Portal BFF, Control Plane, Risk Core, execution adapter, WickHunter, liquidation ingestion, and simulator remain authoritative and independently removable from ASE-00.

## ASE-01 boundary

ASE-01 begins only after exact-head CI is green. Its first task is to replace the temporary call to the Risk Core private deterministic evaluation method with an owner-approved public shadow-evaluation seam, then connect accepted non-synthetic datasets without changing the execution boundary.
