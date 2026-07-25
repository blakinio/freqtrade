---
task_id: FTAI-20260725-rl-v2-seed-validity-diagnosis
status: done
branch: develop
base_branch: develop
created: 2026-07-25
updated: 2026-07-25
related_pr: "299"
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

## Result

All immutable artifacts, embedded configurations, runtime hashes, strategy hashes, raw trade counts and accounting reconcile. No evidence-integrity defect explains the invalid seeds. Seeds `1710810709` and `1950377252` remain invalid at `14` and `13` completed trades and the aggregate remains `inconclusive`.

Both invalid seeds occupied at least one position for `99.9146%` of the execution window, but their median completed-trade durations were `10.176x` and `9.634x` the valid-set median. Their same-pair median flat gaps were not longer than the valid-set medians. The observable association is therefore long-held positions and widely spaced completed-position initiations, not prolonged observed time flat.

The immutable archives contain no per-candle action, prediction or model-state timeline. Causal PPO action-persistence or entry-suppression attribution remains unknown.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-25T23:28:00+02:00
head: b88f8610c71db3f62f63cb4560a579bf9f8f66b0
branch: develop
pr: 299
status: ready
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
  - Develop head 3b3cdd4415acefa83496cceacb922d3868852483 contained the merged bounded diagnosis task before result work.
  - The aggregate, anchor and four new-seed artifact SHA-256 values exactly match the frozen declaration.
  - Every embedded raw backtest configuration reconciles with its accepted effective runtime configuration after the documented extractor normalization.
  - Every seed embeds strategy SHA-256 366785129798d1332ce593f919c54aa23eefb2b15b2d850ab32d5c5cbdf0d5b7 and every new-seed runtime hash matches accepted evidence.
  - Raw trade counts, backtest summaries, accepted descriptive metrics and trade accounting reconcile with maximum per-trade absolute error below 5e-9 USDT.
  - All data coverage records are identical and stop at the exclusive 2026-05-01 boundary; consumed OOS and protected holdout access are false.
  - Seeds 1710810709 and 1950377252 completed 14 and 13 trades and remain invalid below the frozen minimum 20.
  - Both invalid seeds occupied at least one position for 87765 of 87840 minutes, or 99.9146 percent of the execution window.
  - Invalid-seed median completed-trade durations were 10837.5 and 10260 minutes versus the valid-set median 1065 minutes.
  - Invalid-seed initiation rates were 0.2295 and 0.2131 per day versus the valid-set median 0.7377 per day.
  - Invalid-seed same-pair median flat gaps were no longer than valid-set medians for BTC or ETH.
  - The raw archives retain trades, configs, strategy, wallet and market-change files but no per-candle action, prediction or model-state timeline.
  - No model, training, backtest, market-data, cache, baseline or seed operation occurred in this diagnosis.
  - PR 299 was squash-merged to develop as b88f8610c71db3f62f63cb4560a579bf9f8f66b0 with exactly the three declared result paths.
  - The frozen aggregate decision remains inconclusive with strict_oos=false, protected_final_validation=false, profitability non-gating and Phase 6 selected_model=null.
derived:
  - No evidence-integrity defect explains the two invalid seeds.
  - Low completed-trade counts are observationally associated with long-held positions and widely spaced completed-position initiations rather than prolonged observed flat gaps.
  - Near-continuous aggregate occupancy alone is not sufficient because valid seed 1146911492 had even higher occupancy.
  - The two invalid seeds are descriptively similar in occupancy, BTC trade count, target-flat exits, stop-loss exits, force exits and primary mechanism metrics.
  - Completed-trade geometry cannot establish whether PPO repeatedly selected hold or suppressed entries between recorded trades.
unknown:
  - The causal PPO action-level mechanism producing the long completed-position durations remains unknown because the required timeline was not retained.
conflicts: []
first_failure:
  marker: NONE
  evidence: All frozen artifacts and deterministic calculations reconciled; no integrity, provenance, accounting or scope failure was found.
rejected_hypotheses:
  - Rerun, replace or remove either invalid seed.
  - Relax the minimum trade-count gate or reinterpret the frozen aggregate.
  - Treat near-continuous occupancy as causal proof of PPO action persistence.
  - Treat shorter flat gaps as proof of entry suppression or absence of entry suppression.
  - Use descriptive profitability to gate, rank or promote the result.
  - Access consumed historical OOS or the protected final holdout.
  - Execute a model, baseline, seed, data job, cache restore or backtest.
  - Reopen Phase 6 or change selected_model=null.
changed_paths:
  - docs/agents/tasks/FTAI-20260725-rl-v2-seed-validity-diagnosis.md
  - docs/ai_platform/RL_V2_SEED_VALIDITY_DIAGNOSIS.md
  - ai_platform/experimental_model_research/rl-v2-seed-validity-diagnosis-v1.json
validation:
  - command: immutable artifact digest and archive identity verification
    result: PASS
    evidence: Aggregate, anchor and all four new-seed downloaded archive hashes exactly match the prospective declaration.
  - command: deterministic config, strategy, runtime-hash and accounting reconciliation
    result: PASS
    evidence: All configurations and accepted evidence reconcile; maximum per-trade accounting error is below 5e-9 USDT.
  - command: frozen trade-lifecycle geometry calculation
    result: PASS
    evidence: Pair, month, exit, duration, occupancy, initiation and flat-gap metrics were computed only from recorded immutable trades.
  - command: action-level evidence availability inspection
    result: PASS
    evidence: No retained per-candle action or prediction timeline exists, so causal PPO attribution is explicitly recorded as unknown.
  - command: python -m json.tool ai_platform/experimental_model_research/rl-v2-seed-validity-diagnosis-v1.json
    result: PASS
    evidence: The machine-readable diagnosis is valid JSON and preserves the frozen decision and isolation flags.
  - command: AI Platform CI 30175463717 / run 1236
    result: PASS
    evidence: Compile, AI platform tests, Ruff, Ruff format, codespell and JSON validation passed on the final result head.
  - command: Freqtrade CI 30175463684 / run 1460
    result: PASS
    evidence: Scope, pre-commit, documentation syntax, documentation build and CI gate passed on the final result head.
  - command: GitHub Actions Security Analysis 30175463765 / run 1382
    result: PASS
    evidence: Required zizmor workflow-security analysis passed on the final result head.
  - command: python tools/agents/checkpoint.py docs/agents/tasks/FTAI-20260725-rl-v2-seed-validity-diagnosis.md --require-checkpoint
    result: PASS
    evidence: Final exact-content validation completed in AI Platform CI 30175479908, job 89723467818, artifact 8624079260; PR 301 closed without merge.
  - command: squash merge PR 299
    result: PASS
    evidence: GitHub merged the final three-file diagnosis result to develop as b88f8610c71db3f62f63cb4560a579bf9f8f66b0.
blockers: []
next_action: Do not reopen, rerun, replace, retune, rank or promote from this terminal diagnosis; preserve decision=inconclusive and require a separate prospective declaration before any action-level instrumentation or further experiment.
```
