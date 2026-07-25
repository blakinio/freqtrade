---
task_id: FTAI-20260725-rl-v2-seed-validity-diagnosis-declaration
status: active
branch: docs/rl-v2-seed-validity-diagnosis-declaration
base_branch: develop
created: 2026-07-25
updated: 2026-07-25
related_pr: "pending"
owned_paths:
  - docs/agents/tasks/FTAI-20260725-rl-v2-seed-validity-diagnosis-declaration.md
  - docs/ai_platform/RL_V2_SEED_VALIDITY_DIAGNOSIS_DECLARATION.md
  - ai_platform/experimental_model_research/rl-v2-seed-validity-diagnosis-declaration-v1.json
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/tasks/FTAI-20260725-rl-v2-lifecycle-seed-robustness-execution.md
  - docs/ai_platform/RL_V2_LIFECYCLE_SEED_ROBUSTNESS_DECLARATION.md
  - ai_platform/experimental_model_research/rl-v2-lifecycle-seed-robustness-declaration-v1.json
  - ai_platform/experimental_model_research/rl-v2-lifecycle-seed-robustness-execution-contract-v1.json
  - ai_platform/scripts/rl_v2_lifecycle_seed_robustness_evidence.py
search_first:
  - current develop and open PRs overlapping RL-v2 seeds, lifecycle evidence, validity diagnosis, PPO configuration, workflows, run requests or model-selection ownership
optional_reads:
  - ai_platform/freqaimodels/DesiredPositionReinforcementLearner.py
  - ai_platform/strategies/AiDesiredPositionRLLifecycleAlignedResearchStrategy.py
---

# RL-v2 Seed Validity Diagnosis Declaration

## Goal

Prospectively freeze an evidence-only diagnosis of the two low-trade-count seeds from the completed lifecycle seed-robustness study. This declaration defines immutable sources, questions, calculations and causal limits only. It performs no detailed raw-artifact diagnosis and authorizes no execution.

## Frozen source and result

- dedicated workflow run `30171023448` and trigger PR `287`;
- aggregate artifact `rl-v2-lifecycle-seed-robustness-287`, id `8623459762`, digest `sha256:5b39af275b0add9a9d616d6fa8a72132f97844726a69f22fd21c95064ce3b108`;
- frozen aggregate decision `inconclusive`;
- valid seeds `42`, `300538280`, `1146911492`;
- invalid seeds `1710810709` and `1950377252`, with `14` and `13` trades against the frozen minimum `20`;
- all five seeds passed original directional and strong-reduction mechanism criteria;
- seed removal, replacement and rerun remain forbidden.

## Declaration boundaries

- Only immutable aggregate, anchor and four per-seed artifacts may be inspected by a later task.
- Allowed work is deterministic artifact identity, runtime/config, trade-accounting, pair/month/exit, duration, occupancy, initiation and flat-gap diagnosis.
- No model, training, backtest, market-data, cache, baseline or seed operation.
- No validity-threshold relaxation, second seed set, retuning or outcome-aware replacement.
- No causal PPO action-persistence or entry-suppression claim without action-level evidence.
- No consumed OOS or protected final-holdout access.
- No profitability, statistical-proof, ranking, promotion, dry-run or live claim.
- Phase 6 remains complete with authoritative `selected_model=null`.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-25T22:30:00+02:00
head: pending
branch: docs/rl-v2-seed-validity-diagnosis-declaration
pr: pending
status: implementing
context_routes:
  - docs/agents/tasks/FTAI-20260725-rl-v2-lifecycle-seed-robustness-execution.md
  - docs/ai_platform/RL_V2_LIFECYCLE_SEED_ROBUSTNESS_DECLARATION.md
  - ai_platform/experimental_model_research/rl-v2-lifecycle-seed-robustness-declaration-v1.json
  - ai_platform/experimental_model_research/rl-v2-lifecycle-seed-robustness-execution-contract-v1.json
owned_paths:
  - docs/agents/tasks/FTAI-20260725-rl-v2-seed-validity-diagnosis-declaration.md
  - docs/ai_platform/RL_V2_SEED_VALIDITY_DIAGNOSIS_DECLARATION.md
  - ai_platform/experimental_model_research/rl-v2-seed-validity-diagnosis-declaration-v1.json
proven:
  - Develop head 9b2d5331a802cfb70485151f8d062abbea13d8e8 contains the terminal inconclusive seed-robustness checkpoint and no canonical seed request.
  - No open PR containing RL-v2 overlaps seed, lifecycle, PPO, request, workflow, evidence or model-selection ownership.
  - Workflow 30171023448 completed exactly four new seed executions, reused anchor seed 42 without rerun and executed zero baselines.
  - The frozen aggregate decision is inconclusive because seeds 1710810709 and 1950377252 recorded 14 and 13 trades below the declared minimum 20.
  - All five seeds passed the original directional and strong-reduction lifecycle-mechanism criteria.
  - Aggregate and four new-seed artifacts are available with immutable artifact ids and digests recorded in the declaration.
  - This declaration adds no workflow, request, model, strategy, configuration, data or executable analysis code.
  - Classification remains paired historical-development evidence with strict_oos=false, protected_final_validation=false and profitability non-gating.
derived:
  - A bounded artifact diagnosis can separate evidence-integrity defects from descriptive turnover dispersion without changing the frozen decision.
  - Raw completed-trade intervals can quantify occupancy, initiation and flat-gap differences but cannot prove PPO action persistence when action-level timelines are absent.
  - Any future execution or instrumentation change requires another declaration and cannot replace or erase this inconclusive study.
unknown:
  - Whether the immutable raw artifacts contain action-level prediction or action-state timelines sufficient for causal attribution.
  - Whether low completed-trade counts are primarily associated with longer occupancy, fewer completed-position initiations or both.
conflicts: []
first_failure:
  marker: NONE
  evidence: This is an inert declaration task; no detailed artifact diagnosis, model execution, data access, cache operation or threshold change has occurred.
rejected_hypotheses:
  - Rerun or replace the two invalid seeds.
  - Relax the frozen minimum trade-count gate after observing outcomes.
  - Generate a second seed set to overwrite or rescue the completed result.
  - Use profitability or statistical significance to reclassify the aggregate.
  - Attribute sparse trades to PPO behavior without action-level evidence.
  - Access consumed historical OOS or the protected final holdout.
  - Promote, rank, dry-run or deploy from this historical-development evidence.
  - Reopen Phase 6 or change selected_model=null.
changed_paths:
  - docs/agents/tasks/FTAI-20260725-rl-v2-seed-validity-diagnosis-declaration.md
  - docs/ai_platform/RL_V2_SEED_VALIDITY_DIAGNOSIS_DECLARATION.md
  - ai_platform/experimental_model_research/rl-v2-seed-validity-diagnosis-declaration-v1.json
validation:
  - command: live develop and overlapping open-PR search
    result: PASS
    evidence: Develop is 9b2d5331a802cfb70485151f8d062abbea13d8e8 and no open RL-v2 PR exists.
  - command: immutable aggregate and per-seed artifact availability precheck
    result: PASS
    evidence: Aggregate and all four new-seed artifacts were downloadable by exact artifact id; only archive structure and declared summary fields were inspected for feasibility.
  - command: declaration boundary review
    result: PASS
    evidence: The package authorizes no analysis or execution and freezes sources, questions, calculations, causal limits and no-promotion isolation.
  - command: python tools/agents/checkpoint.py docs/agents/tasks/FTAI-20260725-rl-v2-seed-validity-diagnosis-declaration.md --require-checkpoint
    result: NOT_RUN
    evidence: Local checkout is unavailable; repository CI must validate the checkpoint before merge.
blockers: []
next_action: Open and validate the three-file inert declaration PR; merge it only after required CI passes, then declare a separate bounded diagnosis task that inspects exactly the frozen immutable artifacts without any model, data, cache or backtest execution.
```
