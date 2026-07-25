---
task_id: FTAI-20260725-rl-v2-lifecycle-seed-robustness-declaration
status: done
branch: develop
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
updated_at: 2026-07-25T10:25:00+02:00
head: d943a670068484fc6391e17833c20c8abc757ede
branch: develop
pr: 278
status: done
context_routes:
  - docs/agents/tasks/FTAI-20260725-rl-v2-paired-attribution-interpretation.md
  - docs/ai_platform/RL_V2_PAIRED_ATTRIBUTION_INTERPRETATION.md
  - ai_platform/experimental_model_research/rl-v2-paired-attribution-interpretation-v1.json
owned_paths:
  - docs/agents/tasks/FTAI-20260725-rl-v2-lifecycle-seed-robustness-declaration.md
  - docs/ai_platform/RL_V2_LIFECYCLE_SEED_ROBUSTNESS_DECLARATION.md
  - ai_platform/experimental_model_research/rl-v2-lifecycle-seed-robustness-declaration-v1.json
proven:
  - PR 278 froze one immutable anchor seed and four outcome-independent derived seeds without adding execution infrastructure.
  - Anchor seed 42 remains bound to run 30131273189 and artifact digest sha256:11e9d9a8e5f8e65474406524445c7b04fe3d9af5afa6d137847c913f8e66ae04 and must not be rerun.
  - Derived seeds are 300538280, 1710810709, 1950377252 and 1146911492 using the declared digest-word modulo rule.
  - Only freqai.model_training_parameters.seed may differ behaviorally; data-split random_state and all other model, strategy, PPO, reward, feature, threshold, market and geometry inputs remain frozen.
  - Per-seed validity, original directional, strong-reduction and deterministic supported/not-supported/inconclusive rules were declared before additional results exist.
  - The declaration preserves paired historical-development classification, strict_oos=false, protected_final_validation=false, profitability non-gating and Phase 6 selected_model=null.
  - Parallel stale closure PR 277 was closed without merge after canonical interpretation closure PR 276 merged.
  - AI Platform CI 1160, Freqtrade CI 1358 and zizmor 1288 passed on final PR 278 head b9334068bb8d840d3838f398fb8b8b0190a6c7ea.
  - PR 278 was squash-merged to develop as d943a670068484fc6391e17833c20c8abc757ede.
derived:
  - A later valid five-seed evidence set requires only four new executions because seed 42 is an immutable anchor.
  - Seed consistency on reused data can assess stochastic mechanism robustness but cannot create strict-OOS, profitability, statistical-proof, ranking or promotion evidence.
unknown: []
conflicts: []
first_failure:
  marker: NONE
  evidence: Declaration completed as an inert documentation and machine-readable contract package with all required CI green.
rejected_hypotheses:
  - Select or replace seeds after observing outcomes.
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
    evidence: First four digest words map to the four declared non-zero, distinct signed-31-bit seeds and none equals anchor seed 42.
  - command: AI Platform CI 30150922580 / run 1160
    result: PASS
    evidence: AI platform tests, compile, lint, formatting, spelling and JSON validation passed.
  - command: Freqtrade CI 30150922591 / run 1358
    result: PASS
    evidence: Pre-commit, scope classification, documentation syntax, documentation build and CI gate passed.
  - command: GitHub Actions Security Analysis 30150922583 / run 1288
    result: PASS
    evidence: Required zizmor workflow security analysis passed.
  - command: squash merge PR 278
    result: PASS
    evidence: GitHub merged final declaration head b9334068bb8d840d3838f398fb8b8b0190a6c7ea to develop as d943a670068484fc6391e17833c20c8abc757ede.
blockers: []
next_action: Do not reopen this completed declaration task; declare a separate inert seed-robustness infrastructure task only if it implements the frozen seeds, validity and decision rules exactly, performs no model or data execution during review, reruns neither seed 42 nor the baseline, and preserves all OOS, holdout, Phase 6 and no-promotion boundaries.
```
