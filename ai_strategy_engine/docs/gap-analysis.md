# ASE-00 gap analysis

## Baseline

This analysis compares the exactly materialized starter under `ai_strategy_engine/` with the current repository architecture recorded in `ai_strategy_engine/docs/current-state.md`.

The starter is useful research scaffolding, but it is not yet an accepted integration package. The following gaps must be closed without creating parallel portal, risk, execution, bot-management, WickHunter, liquidation, or simulator systems.

## Contracts

### Existing

- `ai_strategy_engine/src/strategy_engine/domain/models.py` defines preliminary `FeatureRecord` and `SignalEvent` models.
- `ai_strategy_engine/schemas/feature-record.v1.schema.json` and `signal-event.v1.schema.json` define initial JSON contracts.
- `ai_platform/portal/contracts/common.py` defines the repository-standard frozen, extra-forbid, UTC-normalized contract base and canonical JSON.
- `ai_platform/portal/contracts/risk.py` defines the canonical `TradeIntent`, `RiskDecision`, `ApprovedExecutionIntent`, and `RejectedExecutionIntent` authority chain.

### Gap

The starter contracts do not yet carry every required field. Missing or incomplete fields include explicit `schema_version`, separate feature/signal version, `idempotency_key`, `configuration_hash`, and structured provenance. `StrategyDefinition`, `ValidationReport`, and `ShadowDecisionEvidence` do not yet exist as typed canonical records.

### Decision

Extend the starter contracts using the portal contract conventions: immutable models, extra fields forbidden, UTC timestamps, deterministic canonical JSON, lowercase SHA-256 validation, stable reason codes, and explicit version fields. Do not redefine portal execution contracts.

## Feature Registry

### Existing

- `ai_strategy_engine/configs/feature_registry.v1.yaml` contains versioned feature metadata, parameters, warm-up, timestamp policy, normalization, AI approval, and license origin.
- `ai_strategy_engine/configs/search_spaces.v1.yaml` contains bounded research parameters.
- `ai_strategy_engine/src/strategy_engine/dsl/validator.py` contains a minimal in-memory `RegistryFeature` representation.

### Gap

There is no production-quality loader that validates YAML structure, resolves dependencies, validates parameter types/ranges/enums/constraints, distinguishes `approved_for_ai` from research-only use, or exposes required sources/warm-up/timestamp/normalization policies.

### Decision

Add one loader in `ai_strategy_engine/src/strategy_engine/registry.py`. It will consume the existing YAML instead of adding another registry. The DSL validator will depend on the loader's typed records.

## Minimal ASE-00 features

### Existing

- corrected and legacy comparison Squeeze: `ai_strategy_engine/src/strategy_engine/features/squeeze.py`;
- Supertrend: `ai_strategy_engine/src/strategy_engine/features/supertrend.py`;
- confirmed pivots: `ai_strategy_engine/src/strategy_engine/features/pivots.py`;
- tests: `ai_strategy_engine/tests/unit/test_squeeze.py`, `test_pivots.py`, and existing trend tests.

### Gap

The baseline tests do not prove a closed-bar-only Supertrend flip/gap contract, confirmed HTF availability, or end-to-end rejection of unconfirmed pivot/HTF records.

### Decision

Retain the existing clean-room feature implementations. Add parity/contract tests and point-in-time feature records rather than creating duplicate indicator providers. Keep `legacy_bug_compatible` test-only and non-default.

## Strategy DSL

### Existing

- JSON Schema: `ai_strategy_engine/schemas/strategy-definition.v1.schema.json`;
- examples under `ai_strategy_engine/examples/`;
- preliminary validator: `ai_strategy_engine/src/strategy_engine/dsl/validator.py`.

### Gap

The validator does not validate all/any/none trees recursively, parameter values against registry and search-space bounds, timeframe membership, confirmation policy, risk policy shape, or complete provenance. It contains an HTF branch that currently does not fail. There is no deterministic condition evaluator.

### Decision

Extend the existing validator and add a declarative evaluator. No `eval()`, `exec()`, generated Python, dynamic imports, or arbitrary callable execution is permitted.

## Leakage Guard

### Existing

- `ai_strategy_engine/src/strategy_engine/validation/leakage.py` rejects `available_at > decision_time` and unconfirmed features and checks append-only replay stability.
- WickHunter independently enforces point-in-time availability in `ai_platform/wickhunter/contracts.py` and dataset acceptance in `ai_platform/wickhunter/dataset.py`.

### Gap

The starter does not yet fail closed for pivot-before-confirmation, incomplete HTF bars, future shifts, target leakage, revised data unavailable point-in-time, final holdout reuse, data-version inconsistency, missing provenance, or mixed configuration/code versions.

### Decision

Extend the existing leakage module with typed validation context and stable reason codes. Do not duplicate WickHunter's historical import or dataset builder.

## Risk Core integration

### Existing

- deterministic limits and snapshot models: `ai_platform/portal/risk/schema.py`;
- deterministic evaluation algorithm: `ai_platform/portal/risk/service.py`;
- canonical outcomes and evidence: `ai_platform/portal/contracts/risk.py`;
- private execution boundary: `ai_platform/portal/contracts/execution.py` and `ai_platform/portal/execution/adapter.py`.

### Gap

The starter has generic position-management helpers but no adapter to the existing Portal Risk Core. A naive implementation would create a duplicate risk decision model or call execution directly.

### Decision

Add a narrow research/shadow adapter under `ai_platform/research/strategy_engine/ase00_adapter.py`. It will map a validated ASE decision to `RiskPolicyLimits` and `RiskEvaluationSnapshot`, invoke the existing deterministic Portal Risk Core evaluation, and persist only `ShadowDecisionEvidence`. It will not construct or submit an `ApprovedExecutionIntent` and will not import the execution adapter.

The current Risk Core exposes the deterministic limit evaluation as a private static method. ASE-00 may use that method only inside the internal adapter and must record this as an ASE-01 hardening item: expose a supported non-persisting shadow evaluation seam from the Risk Core owner.

## Synthetic vertical slice

### Existing

- deterministic WickHunter vertical slice: `ai_platform/wickhunter/`;
- accepted liquidation dataset builder: `ai_platform/wickhunter/dataset.py`;
- deterministic portal simulator: `ai_platform/portal/simulator/`.

### Gap

There is no ASE-specific flow joining point-in-time market/liquidation features, Strategy DSL, Leakage Guard, Portal Risk Core, idempotent replay, and a canonical shadow evidence artifact.

### Decision

Implement one synthetic adapter-owned flow. Inputs are explicitly accepted synthetic fixtures. The flow will reuse the existing Risk Core algorithm and canonical hashing conventions, remain shadow-only, handle duplicate and out-of-order events deterministically, fail closed on missing data, and never create an order.

## Miyagi research package

### Existing

- `ai_strategy_engine/configs/miyagi_parameter_map.v1.yaml`;
- `ai_strategy_engine/docs/MIYAGI_PARAMETER_MAP.md`;
- `ai_strategy_engine/docs/TECHNICAL_AUDIT.md`;
- generic implementations under `ai_strategy_engine/src/strategy_engine/features/` and `risk/position_management.py`.

### Gap

The map must be validated to ensure each visible element is classified only as `confirmed_ui`, `probable`, or `unknown`; the name must not become a production provider identity; and no closed-source parity claim may enter runtime evidence.

### Decision

Keep Miyagi only in research documentation/config provenance. Runtime feature IDs remain generic. Add validation tests for classification and prohibited provider naming.

## Validation and evidence

### Existing

- starter unit/e2e tests under `ai_strategy_engine/tests/`;
- repository E2E and checkpoint conventions under `tests/`, `ai_platform/portal/web/e2e/`, `.github/workflows/`, and `docs/agents/tasks/`.

### Gap

The complete required command set has not yet been run on the integrated package. Negative leakage tests, root integration tests, deterministic restart/replay tests, secret/code scans, JSON/YAML validation, and exact checkpoint hashes are missing.

### Decision

Add a temporary exact-head validation workflow that creates `.venv`, installs `.[dev]`, runs every required command and additional security/contract scans, writes machine-readable and Markdown evidence, commits the checkpoint, then removes itself. PR #584 remains draft until the resulting exact-head CI is green.
