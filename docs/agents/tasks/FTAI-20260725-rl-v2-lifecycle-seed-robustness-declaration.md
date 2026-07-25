---
task_id: FTAI-20260725-rl-v2-lifecycle-seed-robustness-declaration
status: active
branch: docs/rl-v2-lifecycle-seed-robustness-declaration
base_branch: develop
created: 2026-07-25
updated: 2026-07-25
related_pr: "278"
owned_paths:
  - docs/agents/tasks/FTAI-20260725-rl-v2-lifecycle-seed-robustness-declaration.md
  - docs/ai_platform/RL_V2_LIFECYCLE_SEED_ROBUSTNESS_DECLARATION.md
  - ai_platform/experimental_model_research/rl-v2-lifecycle-seed-robustness-declaration-v1.json
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/tasks/FTAI-20260725-rl-v2-paired-attribution-interpretation.md
  - docs/ai_platform/RL_V2_PAIRED_ATTRIBUTION_INTERPRETATION.md
  - ai_platform/experimental_model_research/rl-v2-paired-attribution-interpretation-v1.json
  - ai_platform/experimental_model_research/rl-v2-roi-lifecycle-paired-attribution-execution-contract-v1.json
  - ai_platform/configs/rl_v2_training_research.json
search_first:
  - current develop and open PRs overlapping RL-v2 seeds, lifecycle strategy, PPO configuration, experimental evidence or model-selection ownership
optional_reads:
  - ai_platform/freqaimodels/DesiredPositionReinforcementLearner.py
  - docs/ai_platform/ROADMAP.md
---

# RL-v2 Lifecycle Seed Robustness Declaration

## Goal

Prospectively freeze the only admissible multi-seed robustness question for the unchanged lifecycle-aligned
RL-v2 variant. This task declares identities, seeds, validity rules and mechanism-consistency criteria only.
It does not implement or authorize execution infrastructure.

## Frozen source

- anchor run `30131273189`, trigger PR `#272`;
- anchor artifact `rl-v2-roi-lifecycle-paired-attribution-272`;
- anchor digest `sha256:11e9d9a8e5f8e65474406524445c7b04fe3d9af5afa6d137847c913f8e66ae04`;
- immutable baseline artifact `rl-v2-historical-training-execution-218`, which must not be rerun;
- lifecycle strategy `AiDesiredPositionRLLifecycleAlignedResearchStrategy`;
- model `DesiredPositionReinforcementLearner`;
- reused March-April evidence remains historical-development evidence, not strict OOS.

## Declaration boundaries

- Seed `42` is reused from the immutable anchor and is not rerun.
- Four additional seeds are deterministically derived from the first four 32-bit words of the anchor artifact
  digest, reduced modulo `2147483647`: `300538280`, `1710810709`, `1950377252`, `1146911492`.
- A later execution package may run exactly four new variant executions and zero baseline executions.
- Only `freqai.model_training_parameters.seed` may differ behaviorally by run.
- `freqai.data_split_parameters.random_state=42` and `shuffle=false` remain frozen.
- Per-seed identifiers and artifact paths may vary only for isolation and provenance.
- No consumed historical OOS `20260501-20260630` or protected final holdout `20260801-20260930`.
- No model, strategy, PPO parameter other than seed, reward, feature, threshold, pair, timeframe, fee,
  geometry or policy-semantic change.
- No profitability, statistical-significance, superiority, ranking, promotion, dry-run or live claim.
- Phase 6 remains complete with `selected_model=null`.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-25T10:19:18+02:00
head: a9297e625c1159d02535dd3ff0c121293471da03
branch: docs/rl-v2-lifecycle-seed-robustness-declaration
pr: 278
status: validating
context_routes:
  - docs/agents/tasks/FTAI-20260725-rl-v2-paired-attribution-interpretation.md
  - docs/ai_platform/RL_V2_PAIRED_ATTRIBUTION_INTERPRETATION.md
  - ai_platform/experimental_model_research/rl-v2-paired-attribution-interpretation-v1.json
owned_paths:
  - docs/agents/tasks/FTAI-20260725-rl-v2-lifecycle-seed-robustness-declaration.md
  - docs/ai_platform/RL_V2_LIFECYCLE_SEED_ROBUSTNESS_DECLARATION.md
  - ai_platform/experimental_model_research/rl-v2-lifecycle-seed-robustness-declaration-v1.json
proven:
  - Develop head 9bf961c5adec1d4bbfccaa9316cfddbd7e3d4c5c contains the completed paired-attribution execution, interpretation and canonical closure records.
  - Anchor seed 42 produced 45 non-degenerate trades across both declared pairs and met both frozen mechanism criteria.
  - Anchor artifact digest deterministically yields four additional signed-31-bit seed values without outcome-based selection.
  - Model code passes model_training_parameters.seed into both PPO/runtime parameters and the environment while data_split_parameters.random_state remains independently configurable.
  - Parallel stale closure PR 277 was closed without merge after canonical closure PR 276 merged.
  - PR 278 changes only the seed declaration task, human-readable declaration and machine-readable record; no workflow, model, strategy, config or request file changed.
derived:
  - Reusing seed 42 and executing only four new seeds minimizes duplicate compute while preserving a five-seed evidence set.
  - Seed robustness can evaluate path-level mechanism consistency but cannot create strict-OOS or profitability evidence on reused data.
unknown:
  - Whether all four additional seeds complete valid non-degenerate executions.
  - Whether the lifecycle mechanism reductions remain consistent under the prospectively frozen seed set.
conflicts: []
first_failure:
  marker: NONE
  evidence: Declaration is inert and requires no execution, data or cache access.
rejected_hypotheses:
  - Select seeds manually after observing results.
  - Rerun seed 42 or the immutable baseline.
  - Change data-split random_state together with the PPO seed.
  - Gate on net PnL, profit factor, drawdown, p-value or positive returns.
  - Use consumed historical OOS or the protected final holdout.
  - Treat a five-seed development study as statistical proof, ranking or promotion evidence.
changed_paths:
  - docs/agents/tasks/FTAI-20260725-rl-v2-lifecycle-seed-robustness-declaration.md
  - docs/ai_platform/RL_V2_LIFECYCLE_SEED_ROBUSTNESS_DECLARATION.md
  - ai_platform/experimental_model_research/rl-v2-lifecycle-seed-robustness-declaration-v1.json
validation:
  - command: deterministic seed derivation from immutable anchor digest
    result: PASS
    evidence: First four digest words map to 300538280, 1710810709, 1950377252 and 1146911492 modulo 2147483647; all are non-zero, distinct and different from anchor seed 42.
  - command: current runtime seed-binding inspection
    result: PASS
    evidence: Base config freezes model seed 42 and data-split random_state 42 separately; model pack_env_dict forwards model_training_parameters.seed to the environment.
  - command: compare develop to PR 278 declaration head
    result: PASS
    evidence: Three declaration-only files changed with zero divergence from develop before the checkpoint commit.
blockers: []
next_action: Merge PR 278 only after checkpoint, JSON, documentation and repository CI pass, then close the declaration task in a separate one-file checkpoint PR.
```
