# FTAI-20260808 — WH09 Signal/Data/Model Investigation

```yaml
task_id: FTAI-20260808-wickhunter-wh09-signal-data-model-investigation
project_lane: freqtrade-wickhunter
programme: WickHunter WH09
policy_version: 2
prompting_standard_version: 2.1
task_kind: discovery
feature_scope:
  type: data_pipeline
  user_facing: false
  backend_required: false
  frontend_required: false
  integration_required: true
  e2e_required: false
  completion_claim: internal_only
decomposition_decision: discovery_first
execution_mode: chat_github
run_scope: autonomous_program
continuation_policy: continue_until_real_stop
task_completion_policy: finalize_archive_and_continue
implementation_authorized: false
status: investigating
base_branch: develop
trusted_base_sha: 7b23a958fd4d2bb43569c7f693d2247ef43d1ae9
branch: research/wickhunter-wh09-signal-data-model-investigation-20260808
related_issue: 1384
related_pr: none
invocation_started_at: 2026-08-08T13:48:00+02:00
last_progress_at: 2026-08-08T13:55:00+02:00
ci_checks_for_current_head: 0
unchanged_state_checks: 0
identical_failure_retries: 0
repair_cycles_for_current_gate: 0
context_reconstruction_attempts: 0
stall_warnings: 0
heavy_validation_runs: 0
no_trade_confidence: 0.60
protected_holdout_accessed: false
test_used_for_selection: false
automatic_promotion_enabled: false
trading_credentials_present: false
order_adapter_present: false
execution_enabled: false
orders_submitted: 0
live_capital_authorized: false
```

## Objective

Determine, from trusted WH09 train/validation evidence, why the terminal 900-second replay/model chain cannot produce an independently defensible operational candidate at the frozen `no_trade_confidence=0.60`, and precommit the smallest next scientific work package without lowering the threshold, reusing test/protected-holdout evidence for selection, repeating H900, or starting Runtime/PAPER.

## Trusted starting state

- trusted `develop`: `7b23a958fd4d2bb43569c7f693d2247ef43d1ae9`;
- terminal H900 request-only PR: `#1380`, closed without merge;
- terminal H900 workflow run: `31250937277`, materialization PASS and fresh independent audit PASS;
- H900 artifact: `9020825618`, GitHub digest `sha256:c127c3edfebc75c6f6f5797d65a248803f417489bbcef025c3418046b2b1dc68`;
- source decisions `919`, split-boundary eligible `824`, excluded `95`, labels `1648`;
- model training examples `348`: positives `18`, negatives `330`;
- calibration examples `87`;
- artifact calibration curve maximum probability `0.333333333333`;
- scorer applies calibrated probability and sets risk multiplier to zero whenever calibrated confidence is below the frozen `0.60` threshold;
- terminal test comparison selected `0/162`; `profitability_claimed=false`, `model_promoted=false`.

## Authorization and scope

### Allowed

- read repository code, immutable H900 artifacts and train/validation evidence;
- inspect label prevalence, score distributions, calibration support, feature separability, feature redundancy, model-capacity assumptions, split geometry and class imbalance;
- run deterministic/lightweight analysis using already-produced evidence;
- if existing evidence is insufficient, design at most one new bounded diagnostic using train + validation only, with a precommitted analysis plan and no candidate promotion;
- open one focused discovery PR for durable findings/task state when coherent.

### Forbidden

- lowering or bypassing `no_trade_confidence=0.60`;
- choosing a solution using test or protected holdout outcomes;
- protected holdout access;
- repeating the consumed H900 heavy replay;
- starting candidate-bound Runtime, preflight or a PAPER observation window;
- changing trading credentials, order adapters, execution, promotion, orders or live capital;
- using test results as an optimizer objective, model-family selector, feature selector or calibration selector;
- silently changing the WH09 scientific target or strategy objective.

## Discovery questions

1. Is the immediate `0/162` failure mechanically explained by the calibration ceiling being below `0.60`?
2. Why is calibrated support capped that low: class prevalence, sparse positives, poor raw separation, calibration-bin support, model underfit/overfit, label design, feature insufficiency, or a combination?
3. Do train + validation contain any statistically defensible region with posterior success probability capable of reaching `>=0.60` at meaningful support, without using test/holdout selection?
4. Which existing features carry stable signal across train/validation and which are redundant, unstable or weak?
5. Is the next justified experiment a data/label improvement, feature redesign, model-family/calibration redesign, more independent training data, or a terminal conclusion that current evidence is insufficient?

## Acceptance inventory

The discovery phase is complete only when all are true:

- the confidence ceiling is reproduced from exact artifact/code identities;
- class prevalence and positive support are reported for train and calibration/validation evidence used for model work;
- raw-vs-calibrated score behavior is characterized without using test/protected holdout to choose a solution;
- feature/model/label hypotheses are ranked by evidence, not preference;
- exactly one next scientific work package is precommitted, or the lane records an evidence-based terminal insufficiency result;
- the frozen `0.60` threshold and all zero-authority invariants remain unchanged;
- any related request-only PR is terminal and no unintended related PR remains open.

## Evidence checkpoint 1 — terminal H900 structural finding

`PROVEN` from artifact `9020825618` and `ai_platform/wickhunter/lightgbm_scorer.py` on trusted base:

- training positive prevalence is `18 / 348 = 5.17%`;
- calibration support is `87` cases;
- the persisted monotonic calibration probabilities top out at `0.333333333333`;
- the scorer uses `confidence = calibration.apply(raw_probability)` and sets `risk_multiplier=0` whenever `confidence < 0.60`;
- therefore the persisted H900 model is mechanically incapable of emitting an actionable model score under the frozen threshold, independently of the final test outcomes.

`UNKNOWN` from the packaged artifact alone:

- raw score distributions on train/calibration/validation;
- positive/negative support per calibration bin;
- whether raw separation contains a defensible `>=0.60` posterior region before the current calibration mapping;
- whether the ceiling is primarily data scarcity/class imbalance, calibration design, feature insufficiency, model capacity, label design, or a combination.

The artifact does not package the required per-case feature/score rows. A single bounded runner diagnostic is therefore justified if it remains train+validation-only and does not rematerialize H900 or produce/promote a candidate.

## Context checkpoint

```yaml
phase: investigate
session_id: wh09-signal-data-model-20260808-01
session_role: coordinator-investigator
execution_mode: chat_github
context_pressure: medium
context_growth: stable
context_score: 7
estimate_confidence: medium
decomposition_decision: discovery_first
validation_level: evidence_review
last_completed_step: issue 1384 created and structural confidence-ceiling cause proven from exact H900 artifact plus scorer contract
session_rotation_count: 0
heavy_validation_runs: 0
status: investigating
blocker: none
next_action: design one bounded train+validation-only diagnostic that quantifies raw score separation, calibration-bin support and feature stability without creating a candidate or touching test/protected holdout selection
```
