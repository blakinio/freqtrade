---
task_id: FTAI-20260726-rl-v2-action-observability-execution
status: done
branch: develop
base_branch: develop
created: 2026-07-26
updated: 2026-07-26
related_pr: "345"
owned_paths:
  - docs/agents/tasks/FTAI-20260726-rl-v2-action-observability-execution.md
  - ai_platform/experimental_model_research/run-requests/rl-v2-action-observability-execution-v1.json
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/tasks/FTAI-20260726-rl-v2-action-observability-execution-declaration.md
  - docs/agents/tasks/FTAI-20260726-rl-v2-action-observability-execution-infrastructure.md
  - docs/ai_platform/RL_V2_ACTION_OBSERVABILITY_EXECUTION_DECLARATION.md
  - docs/ai_platform/RL_V2_ACTION_OBSERVABILITY_EXECUTION_INFRASTRUCTURE.md
  - ai_platform/experimental_model_research/rl-v2-action-observability-execution-declaration-v1.json
  - ai_platform/experimental_model_research/rl-v2-action-observability-execution-contract-v1.json
  - ai_platform/scripts/rl_v2_action_observability_execution_run_request.py
  - ai_platform/scripts/rl_v2_action_observability_execution_evidence.py
  - .github/workflows/ai-platform-rl-v2-action-observability-execution.yml
search_first:
  - current develop and open PRs overlapping RL-v2 action observability, lifecycle strategy, PPO configuration, run requests, workflow, data windows, seeds, evidence or model-selection ownership
optional_reads:
  - tests/ai_platform/test_rl_v2_action_observability_execution.py
  - ai_platform/scripts/rl_v2_action_observability.py
---

# RL-v2 Action Observability Execution

## Goal

Execute the merged and prospectively frozen RL-v2 action-observability study through one exact-one-file trigger PR. Download only the declared fresh Kraken history, run exactly the four new seeds once, retain per-candle action telemetry and raw backtest evidence, aggregate descriptive action-versus-position evidence with no automatic decision, and close the trigger PR without merge after terminal evidence is captured.

## Terminal outcome

The bounded execution completed successfully. The exact canonical request was validated, both fresh data jobs proved the declared coverage, all four frozen seed jobs executed exactly once, all raw archives and action timelines passed deterministic evidence validation, and the four-seed aggregate completed with `decision: null`.

Trigger PR 345 was closed without merge. The canonical request therefore remains absent from `develop`.

No seed was replaced, removed or rerun. No prior seed, anchor or baseline was executed. No cache was restored. Consumed historical OOS and the protected final holdout were not accessed.

## Fresh data evidence

| Pair | 15m rows | 1h rows | 4h rows | First candle | Exclusive stop |
|---|---:|---:|---:|---|---|
| BTC/USDT | 14,678 | 3,671 | 919 | 2025-06-01T00:00:00Z | 2025-11-01T00:00:00Z |
| ETH/USDT | 14,640 | 3,672 | 919 | 2025-06-01T00:00:00Z | 2025-11-01T00:00:00Z |

Both coverage reports record `cache_restore_used: false`, `consumed_historical_oos_accessed: false`, and `protected_final_holdout_accessed: false`.

## Four-seed descriptive result

| Seed | Trades | BTC / ETH trades | Accepted target-flat while long | RL target-flat exits | Median duration | Net profit USDT | Timeline SHA-256 |
|---:|---:|---:|---:|---:|---:|---:|---|
| 271828182 | 28 | 11 / 17 | 0 | 0 | 4,200 min | -34.039794 | `c122f42f244d4c97eb90124eb88e309bc79bf2241ae36a2f42b3fcfb0e394dd1` |
| 628318530 | 28 | 11 / 17 | 0 | 0 | 4,200 min | -34.039794 | `c122f42f244d4c97eb90124eb88e309bc79bf2241ae36a2f42b3fcfb0e394dd1` |
| 1414213562 | 47 | 11 / 36 | 20 | 20 | 1,590 min | -39.145257 | `7a2ac4dd7f6b035746d32b319621566f3ba101e2988f445f8cb4be095b308821` |
| 1618033988 | 107 | 11 / 96 | 88 | 88 | 90 min | -58.008576 | `fbe17cb516a4895424e06323b8d93c608caaad95582a0e54752dc30ec9baec23` |

Profitability is descriptive and non-gating. All four net results were negative, but this execution has no profitability, ranking, selection or promotion authority.

Each seed retained exactly 29,378 action-timeline rows. The effective configs are identical after normalizing the frozen seed and runtime identifier. Each run trained fresh BTC and ETH models from scratch on 272 features and 5,682 post-NaN training rows per pair.

For every seed, `accepted_target_flat` while a position was long reconciles exactly with both `exit_long` transitions and `freqai_rl_v2_target_flat` exits: `0`, `0`, `20`, and `88`. This proves the retained action timeline explains the target-flat lifecycle exits for these fresh runs.

The descriptive cross-seed pattern is monotonic in this four-seed sample: more accepted target-flat actions while long coincide with more completed trades and shorter median duration. This is not a statistical or causal claim, cannot be projected to the previously diagnosed invalid seeds, and does not authorize an automatic mechanism decision.

BTC action summaries and BTC trade counts were identical for all four seeds. Seeds `271828182` and `628318530` also produced identical complete action timelines and descriptive trade metrics despite distinct config seeds and isolated runtime identifiers. The evidence does not establish whether this is an expected policy-output collision or a seed-propagation/determinism issue.

## Aggregate result

- aggregate action counts: `target_flat=73,968`, `target_long=43,544`;
- prediction gate counts: `accepted=46,584`, `rejected=70,928`;
- long-state action gates: `accepted_target_flat=108`, `accepted_target_long=43,029`, `rejected_target_flat=0`, `rejected_target_long=142`;
- transitions: `enter_long=266`, `exit_long=108`, `hold_flat=73,967`, `hold_long=43,171`;
- median seed trade count: `37.5`;
- median of seed median durations: `2,895` minutes;
- `decision=null`;
- `automatic_decision=false`;
- `automatic_ranking=false`;
- `automatic_promotion=false`;
- Phase 6 authoritative `selected_model=null`.

## Immutable GitHub Actions evidence

Dedicated workflow: `30195095341`, run number `1`, terminal conclusion `success`, execution head `ca10ddfd981da3a05debcec7a24a5db4ecbbd07c`.

| Artifact | ID | Digest |
|---|---:|---|
| canonical request evidence | 8629844766 | `sha256:088ef8c996c2fea6e764391377fc406f8ace731f29c895dd41cd70ca3ea6df5c` |
| BTC same-run data | 8630133428 | `sha256:3496fff8953518764ef19d7c1b60ce7501a8a80efd6d4f9363d77c3da1bd8983` |
| BTC coverage | 8630133538 | `sha256:8f4540768b03e161701d988e4565aa0a37865869dfccf86fc051766074f573b7` |
| ETH same-run data | 8630136602 | `sha256:712d11d641b27fdd7170da2f10b2b2ef2416e45645b1f2780eb43cdbbfd50e4b` |
| ETH coverage | 8630136716 | `sha256:e71e66b73bdb97c1f17048a52930254fdf52204647df168983eb7b2afdf46e25` |
| seed 271828182 | 8630164034 | `sha256:b80ba3c1d70fba3006935a93c8b838b5a2866b3b41d233ee086b39049220cc62` |
| seed 628318530 | 8630165789 | `sha256:b006a150ec4d9e826ae1cbaf88203f5cd02f784296c1302cc6fa4322796c0fb3` |
| seed 1414213562 | 8630161953 | `sha256:2b6c9eedf51e3e2ef66e46bba8f7e39a00551a11805c00a8691c5c8f368795da` |
| seed 1618033988 | 8630165755 | `sha256:f0943b75b8cbe3b9d249596f49e3431b3428b8d538ab1cecdca1efcf0fe03f2b` |
| four-seed aggregate | 8630167955 | `sha256:4fa9b017f003ef9c3e84e71acd2dbc38cce8d4ab5cef59711a55c908c8909768` |

Raw backtest archive SHA-256 values:

- seed `271828182`: `bd4c6f335d4f1664b21808c28763d97ac7799f756e5ca1255a76d2cc9f32a15f`;
- seed `628318530`: `9d198653b33aad11514ad6782e47229ed98a57456f11d809df4473bafa55a380`;
- seed `1414213562`: `6ea0e8c7c787bfa51ec48194a99ccda5e6aea73895ff2dc57081798ce050bf3d`;
- seed `1618033988`: `7a85b815b973baeb41fa9e5e753c2acab340acf2e2338bcfa52fe0d747dcba96`.

The raw ZIP hashes match the per-seed evidence. Every archive contains the result JSON, effective config, observable strategy source, market-change Feather and wallet Feather.

No `ERROR`, `CRITICAL`, traceback or exception was found in the four retained logs. Each stderr log contains nine non-fatal warnings: one FreqAI exchange-check override, six declared data-start notices, and two further normal runtime notices. The fresh-model logs explicitly state that no existing model, data drawer or historic prediction was found before training.

General Freqtrade CI `30195095355` and zizmor `30195095344` passed on the trigger head. General AI Platform CI `30195095338` failed at its intentional inertness assertion because the canonical request exists on the unmerged execution trigger; the dedicated request-gated workflow is the execution authority and completed successfully.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-26T11:24:00+02:00
head: ca10ddfd981da3a05debcec7a24a5db4ecbbd07c
branch: develop
pr: 345
status: done
context_routes:
  - docs/agents/tasks/FTAI-20260726-rl-v2-action-observability-execution-declaration.md
  - docs/agents/tasks/FTAI-20260726-rl-v2-action-observability-execution-infrastructure.md
  - docs/ai_platform/RL_V2_ACTION_OBSERVABILITY_EXECUTION_DECLARATION.md
  - docs/ai_platform/RL_V2_ACTION_OBSERVABILITY_EXECUTION_INFRASTRUCTURE.md
  - ai_platform/experimental_model_research/rl-v2-action-observability-execution-contract-v1.json
owned_paths:
  - docs/agents/tasks/FTAI-20260726-rl-v2-action-observability-execution.md
  - ai_platform/experimental_model_research/run-requests/rl-v2-action-observability-execution-v1.json
proven:
  - Execution-task declaration PR 343 passed exact-head repository checks and merged as 7163382aad52e59326d02114508f40585252dd01.
  - Diagnostic PR 344 generated the exact canonical request and validated one checkpoint; artifact 8629816822 had digest sha256:03919a2c9c58b77059aa56958b2bb33a875fd4e0f56ad00cdbdf2980c1ca30b1 and the PR closed without merge.
  - Trigger PR 345 added exactly the canonical request file, used execution head ca10ddfd981da3a05debcec7a24a5db4ecbbd07c, reached a terminal state and closed without merge.
  - Request validation, both fresh pair-data jobs, all four frozen seed jobs and the exact-four-seed aggregate completed successfully in dedicated workflow 30195095341.
  - BTC and ETH coverage starts at 2025-06-01T00:00:00Z and reaches the required exclusive stop 2025-11-01T00:00:00Z for 15m, 1h and 4h.
  - Exactly four new seeds executed once each; prior-seed, baseline and anchor execution counts are zero and no outcome-aware rerun or replacement occurred.
  - Every seed used a distinct runtime identifier and config seed, started without an existing model or prediction cache, trained BTC and ETH from scratch, and produced 29378 validated telemetry rows.
  - Effective configs are identical after normalizing only the seed and runtime identifier.
  - Accepted target-flat actions while long equal target-flat lifecycle exits and exit-long transitions exactly for every seed.
  - Seeds 271828182 and 628318530 produced identical complete timelines and descriptive metrics despite distinct config seeds.
  - BTC action summaries and BTC trade counts are identical across all four seeds; observed cross-seed variation is confined to ETH in this matrix.
  - All per-seed archive, config, strategy, model and timeline hashes reconcile with their evidence records.
  - Aggregate evidence records decision null, no automatic ranking or promotion, strict_oos false, protected_final_validation false and profitability non-gating.
  - Cache restore, consumed historical OOS access and protected final holdout access are false in coverage, per-seed and aggregate provenance.
  - Phase 6 remains authoritative with selected_model null.
derived:
  - In this fresh four-seed historical-development sample, accepted target-flat actions while long show a monotonic descriptive association with completed-trade count and an inverse association with median trade duration.
  - The action timeline directly accounts for the target-flat lifecycle exits in these fresh runs, but does not prove why each PPO policy produced its actions.
  - Identical outputs for two distinct seeds and invariant BTC outputs justify a code-first seed-effectiveness and determinism audit before any further model execution.
  - This evidence cannot establish strict-OOS performance, profitability, statistical proof, ranking, selection, deployment readiness or causality for previously diagnosed invalid seeds.
unknown:
  - Whether identical seed 271828182 and 628318530 trajectories are an expected policy-output collision or indicate incomplete seed propagation or another deterministic convergence path.
  - Why BTC produced an identical action timeline across all four seed configs while ETH varied.
  - Whether the descriptive action-duration pattern generalizes outside this single fresh historical-development window.
  - Whether the previously diagnosed invalid seeds would exhibit the same action-level mechanism; those seeds were not rerun.
conflicts: []
first_failure:
  marker: NONE_DEDICATED_EXECUTION
  evidence: Dedicated workflow 30195095341 completed successfully. General AI Platform CI failed only because its intentional request-absence test detects the canonical request on the unmerged trigger PR.
rejected_hypotheses:
  - Rerun, replace or remove either identical-output seed after observing the result.
  - Treat identical timelines as proof of a seed-propagation defect without a separate code-level audit.
  - Project the fresh-run action pattern backward as a causal conclusion for the old invalid seeds.
  - Use negative descriptive profitability as a ranking, rejection, promotion or deployment decision.
  - Access consumed historical OOS or the protected final holdout.
  - Merge the canonical request into develop.
  - Change model, PPO, reward, features, lifecycle semantics, telemetry schema or evidence policy inside this terminal task.
changed_paths:
  - docs/agents/tasks/FTAI-20260726-rl-v2-action-observability-execution.md
validation:
  - command: execution-task declaration PR 343 exact-current-head CI
    result: PASS
    evidence: Freqtrade CI 30194914611 and zizmor 30194914615 passed before squash merge 7163382aad52e59326d02114508f40585252dd01.
  - command: canonical request diagnostic PR 344
    result: PASS
    evidence: Run 30195014883 generated the exact canonical JSON, validated one checkpoint, uploaded artifact 8629816822 and closed without merge.
  - command: dedicated request validation
    result: PASS
    evidence: Job 89775076095 validated exact-one-file scope, checkpoint, request, contract and hashes before data or model access.
  - command: fresh BTC and ETH coverage
    result: PASS
    evidence: Jobs 89775128168 and 89775128162 downloaded, validated and uploaded the declared same-run data without cache restore.
  - command: four frozen seed executions
    result: PASS
    evidence: Jobs 89777709211, 89777709215, 89777709236 and 89777709199 each completed exactly one instrumented training/backtest and evidence extraction.
  - command: exact-four-seed aggregate
    result: PASS
    evidence: Job 89777968960 consumed exactly the four immutable seed artifacts and uploaded aggregate artifact 8630167955 with decision null.
  - command: independent local artifact integrity and log review
    result: PASS
    evidence: Downloaded artifact hashes match GitHub digests; raw ZIP hashes match evidence; all four timelines contain 29378 rows; configs normalize identically; no error, critical, traceback or exception marker exists.
  - command: trigger PR terminal closure
    result: PASS
    evidence: PR 345 closed at 2026-07-26T09:19:34Z with merged false and exactly one changed file.
blockers: []
next_action: Do not rerun, retune, rank or promote this matrix; preserve decision=null and require a separate prospective code-first seed-effectiveness and determinism audit before any further RL-v2 execution, focused on the identical 271828182/628318530 trajectories and invariant BTC outputs without accessing consumed OOS or the protected holdout.
```
