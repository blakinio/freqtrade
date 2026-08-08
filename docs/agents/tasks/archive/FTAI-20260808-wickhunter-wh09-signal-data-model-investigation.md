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
follow_up_implementation_authorized: true
status: completed
base_branch: develop
trusted_base_sha: 7b23a958fd4d2bb43569c7f693d2247ef43d1ae9
branch: research/wickhunter-wh09-signal-data-model-investigation-20260808
related_issue: 1384
related_pr: 1385
diagnostic_run_id: 31256231378
diagnostic_job_id: 93099869458
diagnostic_artifact_id: 9021538934
diagnostic_artifact_digest: sha256:0bc74be9b090115fa0448fcd4698719901c6370422d758e53df4b02c57bf4230
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

## Objective and terminal result

The bounded post-H900 investigation explains why the terminal 900-second model cannot produce a defensible operational candidate at frozen `no_trade_confidence=0.60`, without lowering the threshold, repeating H900, using test/protected holdout for selection, or enabling execution authority.

Authoritative evidence:

- trusted science base: `develop@7b23a958fd4d2bb43569c7f693d2247ef43d1ae9`;
- terminal H900 run `31250937277`, artifact `9020825618`, digest `sha256:c127c3edfebc75c6f6f5797d65a248803f417489bbcef025c3418046b2b1dc68`;
- H900 source decisions `919`, eligible `824`, split-boundary excluded `95`, labels `1648`;
- H900 terminal comparison selected `0/162`; no candidate was promoted;
- bounded diagnostic run `31256231378`, job `93099869458`, conclusion `SUCCESS`;
- diagnostic artifact `9021538934`, digest `sha256:0bc74be9b090115fa0448fcd4698719901c6370422d758e53df4b02c57bf4230`;
- diagnostic opened train and validation only; `test_partition_files_opened=0`, `protected_holdout_accessed=false`, `test_used_for_selection=false`.

## Scientific findings

Train:

- support `348`;
- positives `18` (`5.17%`);
- raw AUC `0.998569`;
- raw maximum probability `0.686309`;
- raw scores `>=0.60`: `5`;
- calibrated scores `>=0.60`: `0`.

Validation:

- support `87`;
- positives `7` (`8.05%`);
- raw AUC `0.811607`;
- raw maximum probability `0.331543`;
- raw scores `>=0.60`: `0`;
- calibrated scores `>=0.60`: `0`.

Supported validation regions remain below the frozen gate:

- top `10`: `3/10`, Laplace `0.333333`, Wilson lower 95% `0.107791`;
- top `20`: `6/20`, Laplace `0.318182`, Wilson lower 95% `0.145477`;
- best validation calibration bin with support `>=10`: Laplace `0.096386`;
- persisted calibrated maximum: `0.333333333333`.

The immediate zero-action behavior is mechanically caused by the calibrated confidence ceiling below `0.60`, but calibration alone is not an admissible repair: validation generalization is materially weaker than train and positive support is sparse. The evidence supports growth of independent chronological live evidence with controlled retraining, not repeated retraining on the same static sample and not threshold lowering. Existing signal should be retained and challenged rather than discarded; notable stable univariate features include `liquidation_burst_intensity`, `volatility_ratio`, and `maximum_event_zscore`.

## Next work package

`NEXT_WORK_PACKAGE: WH09_PRODUCTION_RESEARCH_RUNTIME`

The durable owner handover recorded on Issue `#1384` defines a zero-execution research/shadow continuation: continuously collect production market evidence, run observation-only shadow inference, persist all decisions including `NO_TRADE`, materialize immutable outcomes after the frozen `900 s` horizon, grow a chronological research dataset, expose operator telemetry, and introduce bounded challenger retraining only after provenance/labeling are proven. PAPER/demo position execution remains candidate-gated; automatic promotion, real exchange orders and live capital remain forbidden.

This archive record does not itself expand production or live-capital authority. The follow-up invocation must re-resolve authority from the trusted owner/system/governance chain before any production mutation.

## Closeout

```yaml
closeout:
  scientific_discovery_complete: true
  diagnostic_outcome_verified: true
  h900_repeated: false
  threshold_changed: false
  test_used_for_selection: false
  protected_holdout_accessed: false
  candidate_materialized: false
  automatic_promotion_enabled: false
  execution_enabled: false
  orders_submitted: 0
  live_capital_authorized: false
  runtime_e2e:
    result: NOT_APPLICABLE
    reason: discovery consumed immutable H900 and train-validation diagnostic evidence; no runtime mutation was part of this task
  related_request_prs:
    - PR 1380 closed request-only after terminal H900 evidence
  next_work_package: WH09_PRODUCTION_RESEARCH_RUNTIME
```

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-08-08T16:01:36+02:00
head: containing_commit
branch: research/wickhunter-wh09-signal-data-model-investigation-20260808
pr: 1385
status: completed
context_routes:
  - docs/agents/prompts/WICKHUNTER_WH09_PARALLEL_AGENTS.md
  - docs/agents/PROMPTING_STANDARD.md
  - docs/agents/PROMPTING_HANDOVER.md
owned_paths:
  - docs/agents/tasks/archive/FTAI-20260808-wickhunter-wh09-signal-data-model-investigation.md
proven:
  - H900 run 31250937277 completed with no operational candidate selected from 162 validation comparison cases
  - diagnostic run 31256231378 completed SUCCESS using train and validation only
  - validation raw maximum probability was 0.331543 and calibrated maximum remained below the frozen 0.60 gate
  - no supported train-validation region justified posterior success probability at or above 0.60
  - test partition outcomes and protected holdout were not used for scientific selection
  - no candidate promotion execution orders or live-capital authority occurred
derived:
  - calibration ceiling explains immediate zero-action behavior but is not the sole scientific limitation
  - sparse positive support and train-validation generalization gap require additional independent chronological evidence
  - the single next scientific work package is WH09_PRODUCTION_RESEARCH_RUNTIME
unknown:
  - exact missing implementation seams for the production research runtime require follow-up inventory on trusted develop
conflicts: []
first_failure:
  marker: closeout_governance_defect
  evidence: PR 1385 initially used a disallowed research title and an incomplete durable checkpoint; both are repaired in closeout
rejected_hypotheses:
  - lower no_trade_confidence below 0.60 to manufacture activity
  - rerun the consumed H900 materialization on the same scientific hypothesis
  - calibration-only repair is sufficient despite unsupported validation probability
  - repeated retraining on the unchanged static sample is justified
changed_paths:
  - docs/agents/tasks/archive/FTAI-20260808-wickhunter-wh09-signal-data-model-investigation.md
validation:
  - command: trusted H900 workflow run 31250937277
    result: PASS
    evidence: artifact 9020825618 independently inspected with materialization and audit PASS
  - command: bounded train-validation diagnostic run 31256231378
    result: PASS
    evidence: artifact 9021538934 digest sha256:0bc74be9b090115fa0448fcd4698719901c6370422d758e53df4b02c57bf4230
  - command: runtime E2E for this discovery task
    result: NOT_APPLICABLE
    evidence: no runtime product or deployment mutation belongs to this discovery-only closeout
blockers: []
next_action: Start the single governed WH09_PRODUCTION_RESEARCH_RUNTIME follow-up lane from this terminal evidence after PR 1385 merges.
```
