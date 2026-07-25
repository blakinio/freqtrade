---
task_id: FTAI-20260725-rl-v2-seed-validity-diagnosis
status: active
branch: docs/rl-v2-seed-validity-diagnosis-task
base_branch: develop
created: 2026-07-25
updated: 2026-07-25
related_pr: "296"
owned_paths:
  - docs/agents/tasks/FTAI-20260725-rl-v2-seed-validity-diagnosis.md
  - docs/ai_platform/RL_V2_SEED_VALIDITY_DIAGNOSIS.md
  - ai_platform/experimental_model_research/rl-v2-seed-validity-diagnosis-v1.json
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/tasks/FTAI-20260725-rl-v2-seed-validity-diagnosis-declaration.md
  - docs/ai_platform/RL_V2_SEED_VALIDITY_DIAGNOSIS_DECLARATION.md
  - ai_platform/experimental_model_research/rl-v2-seed-validity-diagnosis-declaration-v1.json
  - docs/agents/tasks/FTAI-20260725-rl-v2-lifecycle-seed-robustness-execution.md
  - ai_platform/scripts/rl_v2_lifecycle_seed_robustness_evidence.py
search_first:
  - current develop and open PRs overlapping RL-v2 seed artifacts, validity diagnosis, lifecycle evidence, PPO configuration, workflows, run requests or model-selection ownership
optional_reads:
  - ai_platform/freqaimodels/DesiredPositionReinforcementLearner.py
  - ai_platform/strategies/AiDesiredPositionRLLifecycleAlignedResearchStrategy.py
---

# RL-v2 Seed Validity Diagnosis

## Goal

Perform the prospectively declared evidence-only diagnosis of the two low-trade-count seeds from the completed lifecycle seed-robustness study. The task may inspect only immutable artifacts and must produce one documentation result plus one machine-readable evidence file. It performs no model, training, backtest, market-data or cache operation.

## Frozen evidence set

- aggregate workflow run `30171023448`, artifact id `8623459762`, digest `sha256:5b39af275b0add9a9d616d6fa8a72132f97844726a69f22fd21c95064ce3b108`;
- anchor seed `42`, run `30131273189`, artifact digest `sha256:11e9d9a8e5f8e65474406524445c7b04fe3d9af5afa6d137847c913f8e66ae04`;
- seed `300538280`, artifact id `8623454828`, digest `sha256:6b4a74e15cf1cd7eb1d77d348fc21211f6f9b8da4f661f05332a77b22ea322ca`;
- seed `1710810709`, artifact id `8623457962`, digest `sha256:6cda21cc5c512387936992609b61514c843b2e9871e819ff9b6e048715a4c581`;
- seed `1950377252`, artifact id `8623457885`, digest `sha256:e8570fb4fc03721775d42ffe2e65b7e917801076b30a73923ed58b04488f983a`;
- seed `1146911492`, artifact id `8623455361`, digest `sha256:7b056e6b6e64863aa46191bb854f534482cd288fb4ef5fa44ca76fa723db4d86`.

## Required outputs

- deterministic artifact identity, config and trade-accounting reconciliation;
- pair, realized-month, exit-reason and duration decomposition for every seed;
- occupied-time, completed-position initiation and same-pair flat-gap comparisons;
- exact invalid-seed versus valid-set-median ratios and differences;
- explicit statement whether action-level timelines exist and whether causal PPO attribution is possible;
- preservation of the frozen `inconclusive` decision and all no-rerun, OOS, holdout, Phase 6 and no-promotion boundaries.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-25T22:54:00+02:00
head: a4326c7a7fd1b2b95b930085ee7cbe35ee0e8b10
branch: docs/rl-v2-seed-validity-diagnosis-task
pr: 296
status: validating
context_routes:
  - docs/agents/tasks/FTAI-20260725-rl-v2-seed-validity-diagnosis-declaration.md
  - docs/ai_platform/RL_V2_SEED_VALIDITY_DIAGNOSIS_DECLARATION.md
  - ai_platform/experimental_model_research/rl-v2-seed-validity-diagnosis-declaration-v1.json
  - docs/agents/tasks/FTAI-20260725-rl-v2-lifecycle-seed-robustness-execution.md
owned_paths:
  - docs/agents/tasks/FTAI-20260725-rl-v2-seed-validity-diagnosis.md
  - docs/ai_platform/RL_V2_SEED_VALIDITY_DIAGNOSIS.md
  - ai_platform/experimental_model_research/rl-v2-seed-validity-diagnosis-v1.json
proven:
  - Develop head c6c3a6ca1a0245118e8e4e13db0cb4ec6e9716b3 contains the completed prospective diagnosis declaration and its closed checkpoint.
  - No open PR containing RL-v2 overlaps seed artifacts, lifecycle evidence, PPO configuration, workflows, requests or model-selection ownership.
  - The frozen aggregate decision remains inconclusive with valid seeds 42, 300538280 and 1146911492 and invalid seeds 1710810709 and 1950377252.
  - Seed removal, replacement, rerun and validity-threshold relaxation are forbidden.
  - The declaration binds this diagnosis to exactly one aggregate, one anchor and four new-seed immutable artifacts.
  - The required outputs are deterministic artifact, accounting, trade-lifecycle and evidence-availability calculations only.
  - This task declaration adds no result file, workflow, request, model, strategy, configuration or executable analysis code.
  - Classification remains paired_historical_development_seed_validity_diagnosis with strict_oos=false, protected_final_validation=false and profitability non-gating.
derived:
  - The diagnosis can determine whether raw artifacts reconcile and quantify completed-trade turnover dispersion without executing another experiment.
  - Completed-trade intervals can separate observed occupancy duration from completed-position initiation frequency but cannot expose unrecorded action decisions.
  - Missing action-level evidence must remain unknown and cannot be replaced by a causal PPO inference.
unknown:
  - Whether the anchor artifact remains downloadable by exact immutable artifact id and digest.
  - Whether the raw archives contain any action-level prediction or action-state timeline.
  - Whether invalid-seed turnover dispersion is associated mainly with occupancy duration, completed-position initiation spacing or both.
conflicts: []
first_failure:
  marker: NONE
  evidence: This one-file task declaration performs no artifact download, detailed diagnosis, data access, cache operation or model execution.
rejected_hypotheses:
  - Rerun, replace or remove either invalid seed.
  - Relax the minimum trade-count gate or reinterpret the frozen aggregate.
  - Download market data or restore research caches.
  - Execute a baseline, anchor, new seed, training job or backtest.
  - Claim PPO action persistence or entry suppression without action-level evidence.
  - Gate, rank or promote on descriptive profitability metrics.
  - Access consumed historical OOS or the protected final holdout.
  - Reopen Phase 6 or change selected_model=null.
changed_paths:
  - docs/agents/tasks/FTAI-20260725-rl-v2-seed-validity-diagnosis.md
validation:
  - command: live develop and overlapping open-PR search
    result: PASS
    evidence: Develop is c6c3a6ca1a0245118e8e4e13db0cb4ec6e9716b3 and no open RL-v2 PR exists before this task declaration.
  - command: diagnosis declaration boundary review
    result: PASS
    evidence: The merged declaration fixes immutable sources, calculations, causal limits, output paths and all execution prohibitions.
  - command: python tools/agents/checkpoint.py docs/agents/tasks/FTAI-20260725-rl-v2-seed-validity-diagnosis.md --require-checkpoint
    result: NOT_RUN
    evidence: Local checkout is unavailable; repository CI must validate the task checkpoint before merge.
blockers: []
next_action: Open and validate this exact-one-file diagnosis task declaration PR; merge it only after required CI and checkpoint validation pass, then branch from updated develop, inspect exactly the frozen immutable artifacts, and add only the declared diagnosis documentation, machine-readable evidence and task-record updates.
```
