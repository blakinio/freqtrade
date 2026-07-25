# RL-v2 Seed Validity Diagnosis Declaration

## Purpose

The completed lifecycle seed-robustness study produced the frozen aggregate decision `inconclusive` because seeds `1710810709` and `1950377252` completed only `14` and `13` trades, below the prospectively declared minimum of `20`. All five seeds nevertheless passed the original directional and strong lifecycle-mechanism criteria.

This declaration freezes a separate evidence-only diagnosis before any detailed inspection of the raw per-seed archives. It authorizes no model execution, backtest, market-data access, cache restore, seed replacement, validity-threshold change, ranking or promotion.

## Immutable evidence set

The later diagnosis may use only the following completed artifacts:

- aggregate workflow run `30171023448`, artifact `rl-v2-lifecycle-seed-robustness-287`, artifact id `8623459762`, digest `sha256:5b39af275b0add9a9d616d6fa8a72132f97844726a69f22fd21c95064ce3b108`;
- immutable anchor seed `42`, workflow run `30131273189`, artifact `rl-v2-roi-lifecycle-paired-attribution-272`, digest `sha256:11e9d9a8e5f8e65474406524445c7b04fe3d9af5afa6d137847c913f8e66ae04`;
- seed `300538280`, artifact id `8623454828`, digest `sha256:6b4a74e15cf1cd7eb1d77d348fc21211f6f9b8da4f661f05332a77b22ea322ca`;
- seed `1710810709`, artifact id `8623457962`, digest `sha256:6cda21cc5c512387936992609b61514c843b2e9871e819ff9b6e048715a4c581`;
- seed `1950377252`, artifact id `8623457885`, digest `sha256:e8570fb4fc03721775d42ffe2e65b7e917801076b30a73923ed58b04488f983a`;
- seed `1146911492`, artifact id `8623455361`, digest `sha256:7b056e6b6e64863aa46191bb854f534482cd288fb4ef5fa44ca76fa723db4d86`.

The valid comparison set is seeds `42`, `300538280` and `1146911492`. The invalid set is exactly seeds `1710810709` and `1950377252`. No seed may be removed, replaced or rerun.

## Frozen diagnostic questions

A later diagnosis must answer only these questions:

1. Do artifact digests, metadata, effective runtime configurations, raw result configurations, trade accounting and aggregate evidence reconcile without defect?
2. How do completed-trade counts decompose by pair, realized month, exit reason and trade duration for every seed?
3. How much of the turnover dispersion is observable as position-occupancy duration versus completed-position initiation frequency and flat-gap spacing?
4. Are the two invalid seeds similar to each other on those descriptive dimensions, and how do they differ from the three valid seeds?
5. Does the immutable evidence contain enough action-level information to attribute low trade count to PPO action persistence or entry suppression? If not, that causal question must remain `unknown`.

## Frozen calculations

The later diagnosis may calculate only deterministic quantities from recorded artifacts:

- trade-count and pair/month/exit-reason decompositions;
- gross-price PnL, recorded fees and net PnL reconciliation;
- duration quantiles and total occupied minutes by pair;
- union-of-trade-interval occupied minutes where overlaps exist;
- completed-position initiation timestamps and inter-initiation intervals;
- flat gaps between one completed trade and the next same-pair completed trade;
- ratios and absolute differences between each invalid seed and the median of the valid comparison set;
- log/config warning inventory limited to evidence integrity and runtime behavior already recorded by the completed runs.

No post-hoc pass threshold, replacement rule, profitability gate or model-selection score may be introduced. The diagnosis reports quantities and evidence limitations; it does not reclassify the frozen aggregate result.

## Evidence classification and boundaries

All outputs remain:

- `paired_historical_development_seed_validity_diagnosis`;
- `strict_oos=false`;
- `protected_final_validation=false`;
- profitability non-gating and descriptive only;
- ineligible for statistical-proof, superiority, ranking, promotion, dry-run or live claims.

The consumed historical OOS window `20260501-20260630` and protected final holdout `20260801-20260930` remain forbidden. Phase 6 remains complete with authoritative `selected_model=null`.

## Completion rule

A later diagnosis is `complete` only if every immutable artifact is identity-verified, all available raw trades and configurations reconcile, and all frozen descriptive calculations are recorded. It is `blocked` if an artifact is unavailable or evidence integrity cannot be reconciled. Either outcome leaves the lifecycle seed-robustness decision `inconclusive` unchanged.

## Future boundary

This declaration does not authorize the diagnosis itself. A separate bounded diagnosis task must perform the inspection and record results in one documentation file and one machine-readable evidence file. That task may not execute or rerun a seed, baseline, model, backtest, data job or cache operation. Any later experiment or instrumentation change requires another prospective declaration and cannot erase or replace the completed seed-robustness result.
