# RL-v2 Lifecycle Seed Robustness Infrastructure

## Purpose

This package implements the fail-closed infrastructure required to evaluate the prospectively frozen
five-seed lifecycle mechanism question. It contains no canonical request and therefore performs no model
training, backtest, market-data download, exchange access or cache restore during review.

The infrastructure is not a promotion pipeline. Its only future output is
`paired_historical_development_seed_robustness` evidence on a reused development window.

## Frozen evidence geometry

The aggregate evidence set contains:

- immutable anchor seed `42`, reused from workflow run `30131273189`;
- new seed `300538280`;
- new seed `1710810709`;
- new seed `1950377252`;
- new seed `1146911492`.

The anchor seed is embedded through its immutable artifact identity and metrics. It is never downloaded or
rerun by this workflow. The immutable historical baseline is also never rerun.

A later valid trigger executes exactly four Freqtrade backtesting commands: one per new seed. Matrix
parallelism does not change the declared command count.

## Infrastructure components

### Execution contract

`ai_platform/experimental_model_research/rl-v2-lifecycle-seed-robustness-execution-contract-v1.json`
binds:

- the completed seed declaration and its merge identities;
- immutable anchor and baseline artifacts;
- ordered seed identities and exact execution counts;
- model, lifecycle strategy and base-config SHA-256 values;
- the only behavioral degree of freedom;
- temporal and market-data geometry;
- non-degeneracy, directional and strong-reduction criteria;
- evidence classification and deterministic decision values;
- OOS, final-holdout, Phase 6 and no-promotion boundaries.

### Canonical request guard

`ai_platform.scripts.rl_v2_lifecycle_seed_robustness_run_request`:

- validates the contract and completed declaration;
- revalidates the original paired lifecycle contract;
- verifies exact model, strategy and config hashes;
- rejects anchor seed `42`, unknown seeds and any changed seed set;
- emits one canonical exact-scope request;
- requires byte-for-byte semantic equality when loading a request;
- materializes an isolated temporary runtime config for exactly one declared new seed;
- changes only the lifecycle strategy, per-seed identifier, train/backtest geometry and
  `freqai.model_training_parameters.seed`;
- keeps `freqai.data_split_parameters.random_state=42` and `shuffle=false`;
- delegates pre-OOS data verification to the already repaired paired-attribution verifier.

The canonical request path is intentionally absent from this package:

`ai_platform/experimental_model_research/run-requests/rl-v2-lifecycle-seed-robustness-execution-v1.json`

### Evidence extraction

`ai_platform.scripts.rl_v2_lifecycle_seed_robustness_evidence` has two fail-closed modes.

`extract` validates one new-seed archive, reconciles raw trade accounting, computes the original lifecycle
metrics, and applies the frozen non-degeneracy gate:

- both BTC/USDT and ETH/USDT must trade;
- total trades must be at least `20`;
- at least one target-flat exit must remain active;
- rejected signals and timed-out orders must remain zero;
- runtime, temporal, long-only, fee, ROI and stop-loss identities must reconcile.

A seed that fails non-degeneracy remains recorded as invalid. It is not silently discarded and cannot be
replaced.

`aggregate` accepts exactly four unique new-seed evidence files, injects the immutable seed-42 anchor, and
computes the declared decision:

- `supported` when all five seeds are valid, every seed passes both original directional criteria, and at
  least four seeds pass both strong-reduction criteria;
- `not_supported` when all seeds are valid but consistency fails;
- `inconclusive` when any seed fails execution, provenance, accounting or non-degeneracy validation.

Profit, profit factor, drawdown and other trading metrics are preserved only as descriptive arrays and
medians. They cannot affect the decision.

### Request-triggered workflow

`.github/workflows/ai-platform-rl-v2-lifecycle-seed-robustness.yml` runs only when a pull request is opened
against `develop` and adds the exact canonical request path.

Before runtime installation or data access, the workflow verifies that the PR contains exactly one added
file and validates a separately declared execution checkpoint.

The workflow then:

1. validates and uploads canonical request evidence;
2. prepares and verifies the already declared pre-OOS BTC and ETH data;
3. executes one isolated matrix job for each of the four new seeds;
4. extracts and uploads one immutable artifact per seed;
5. downloads those four same-run artifacts using pinned
   `actions/download-artifact@3e5f45b2cfb9172054b4087a40e8e0b5a5461e7c`;
6. combines them with the immutable seed-42 anchor;
7. uploads one aggregate five-seed decision artifact.

The workflow contains no baseline command and no seed-42 command.

## Review-time inertness

This infrastructure PR cannot trigger the seed workflow because it does not add the canonical request.
Standard repository CI may compile code, run dependency-light tests, validate JSON, inspect workflow
security and build documentation. Those checks do not install the RL runtime or access model data through
the seed workflow.

After infrastructure merge, this task must close. A separate documentation-only execution task must then
be declared and merged at the contract-bound path:

`docs/agents/tasks/FTAI-20260725-rl-v2-lifecycle-seed-robustness-execution.md`

Only after that checkpoint exists may a fresh branch generate the canonical request and open an
exact-one-file trigger PR. The trigger must be closed without merge after terminal evidence is collected.

## Boundaries retained

- Seed `42` is not rerun.
- The historical baseline is not rerun.
- No seed can be replaced after an invalid or unfavorable result.
- Only the PPO/runtime seed changes behaviorally.
- The data split remains fixed at random state `42` with no shuffle.
- Consumed historical OOS `20260501-20260630` remains forbidden.
- Protected final holdout `20260801-20260930` remains forbidden.
- Evidence is not strict OOS or protected final validation.
- Profitability and statistical significance are non-gating.
- No ranking, superiority, promotion, dry-run or live conclusion is authorized.
- Phase 6 remains complete with authoritative `selected_model=null`.
