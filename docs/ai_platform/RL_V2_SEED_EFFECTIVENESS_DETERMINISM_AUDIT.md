# RL-v2 Seed Effectiveness And Determinism Audit

## Status

`code_audit_complete_no_seed_propagation_defect_proven`

This is a static repository audit. It performs no data access, model training, backtest, inference, replay or seed rerun.

## Why this audit exists

The completed action-observability matrix produced two notable collisions:

- seeds `271828182` and `628318530` retained identical complete action timelines and descriptive trade results;
- BTC/USDT retained the same action summary and 11 completed trades for all four seeds.

Those observations justified a code-first audit, but they did not by themselves prove that the runtime ignored or dropped the configured seed.

## Audited seed path

### 1. Runtime materialization

`materialize_runtime_config()` starts from the frozen research config, assigns a seed-specific FreqAI identifier and replaces `freqai.model_training_parameters.seed` with the declared execution seed. It preserves PPO `n_steps=128`, `batch_size=64`, data-split `random_state=42` and `shuffle=false`.

**Finding:** the declared seed is present in every isolated runtime config.

### 2. Project model adapter

`DesiredPositionReinforcementLearner.pack_env_dict()` reads `model_training_parameters.seed`, converts it to an integer and places the same value in the training/evaluation environment dictionary.

**Finding:** the project adapter does not discard the seed before environment construction.

### 3. PPO constructor

The inherited `ReinforcementLearner.fit()` expands all `model_training_parameters` into the Stable-Baselines3 PPO constructor.

**Finding:** the seed reaches the PPO constructor together with `n_steps` and `batch_size`.

### 4. Environment seeding

`BaseEnvironment.__init__()` calls `self.seed(seed)`, and `seed()` initializes the Gymnasium NumPy generator through `seeding.np_random(seed)`.

The environment also contains a Python-global `random.randint()` branch for randomized episode starts. The completed matrix froze `randomize_starting_position=false`, so that branch was inactive.

**Finding:** the active completed path supplies the seed to the environment and does not enter the identified global-random start branch.

### 5. Stable-Baselines3 source review

The inspected official Stable-Baselines3 on-policy source at commit `06f613544574aa3157eba0ccee8570f5a8a8e1c9` calls `set_random_seed(self.seed)` before policy construction. Its base implementation seeds Python, NumPy, PyTorch, the action space and the environment.

The completed execution did not retain the exact installed Stable-Baselines3 or Torch versions, so this source review supports the expected library behavior but is not proof of the exact dependency bytes used by workflow run `30195095341`.

## Answers to the audit questions

| Question | Finding |
|---|---|
| Did materialization replace the base seed? | Yes. |
| Did the project model pass it to the environment? | Yes. |
| Did the inherited learner pass it to PPO? | Yes. |
| Does inspected SB3 seed before policy construction? | Yes, in the reviewed official source. Exact completed-runtime version was not retained. |
| Was an identified unseeded random branch active? | No. `randomize_starting_position` was false. |
| Can retained evidence distinguish identical policies from identical actions? | No. Policy parameter/state digests and serialized trained policies were not retained. |

## Bounded conclusion

Repository evidence supports effective seed wiring. It does **not** support an incomplete-seed-propagation defect, and it does not authorize a runtime code change.

The identical timelines remain unexplained. They are compatible with at least:

- distinct or identical trained policies choosing the same deterministic actions;
- deterministic convergence under the short frozen training geometry;
- pair-specific action-boundary saturation, especially for invariant BTC outputs.

This audit cannot choose among those explanations because the completed execution did not retain exact dependency versions, device/determinism flags, initial or final policy-state digests, or serialized trained policy artifacts.

## Required provenance before any future RL execution

A separate prospective contract must require, per run and per pair:

- exact Python and dependency versions, including Stable-Baselines3 and Torch, with immutable hashes;
- device and Torch deterministic-algorithm flags;
- effective runtime-config digest;
- seed and RNG provenance;
- initial policy-state digest before learning;
- final policy-state digest after learning;
- serialized trained-policy artifact digest.

Those additions can make a later run diagnostically stronger. They do not authorize repeating the completed four-seed matrix or accessing consumed OOS or the protected final holdout.

## Governance

- no model or backtest was run;
- no market data or cache was accessed;
- no seed was repeated or replaced;
- no upstream Freqtrade code was modified;
- no PPO, reward, feature, lifecycle, strategy or workflow behavior changed;
- no ranking, selection, promotion, dry-run or live action is authorized;
- Phase 6 remains authoritative with `selected_model=null`.
