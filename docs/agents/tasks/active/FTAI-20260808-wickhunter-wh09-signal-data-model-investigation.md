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
status: ready_for_closeout
base_branch: develop
trusted_base_sha: 7b23a958fd4d2bb43569c7f693d2247ef43d1ae9
branch: research/wickhunter-wh09-signal-data-model-investigation-20260808
related_issue: 1384
related_pr: 1385
diagnostic_run_id: 31256231378
diagnostic_job_id: 93099869458
diagnostic_artifact_id: 9021538934
diagnostic_artifact_digest: sha256:0bc74be9b090115fa0448fcd4698719901c6370422d758e53df4b02c57bf4230
invocation_started_at: 2026-08-08T13:48:00+02:00
last_progress_at: 2026-08-08T15:38:00+02:00
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

Explain why the terminal WH09 H900 model cannot produce a defensible operational candidate at frozen `no_trade_confidence=0.60`, then hand over exactly one evidence-backed next work package without lowering the threshold, using test/protected holdout for selection, repeating H900, or enabling real-capital execution.

## Trusted starting state

- trusted science base: `develop@7b23a958fd4d2bb43569c7f693d2247ef43d1ae9`;
- terminal H900 request-only PR `#1380` closed without merge;
- H900 run `31250937277`: materialization PASS + independent audit PASS;
- H900 artifact `9020825618`, digest `sha256:c127c3edfebc75c6f6f5797d65a248803f417489bbcef025c3418046b2b1dc68`;
- H900 source decisions `919`, eligible `824`, split-boundary excluded `95`, labels `1648`;
- H900 model train examples `348`, positives `18` (`5.17%`);
- persisted calibration max `0.333333333333`;
- frozen `no_trade_confidence=0.60`;
- terminal comparison selected `0/162`, `profitability_claimed=false`, `model_promoted=false`.

## Terminal bounded diagnostic

Authoritative diagnostic:

- run `31256231378`;
- job `93099869458`;
- conclusion `SUCCESS`;
- evidence artifact `9021538934`;
- digest `sha256:0bc74be9b090115fa0448fcd4698719901c6370422d758e53df4b02c57bf4230`;
- analysis splits: `train`, `validation` only;
- `model_retrained=false`;
- `candidate_materialized=false`;
- `test_partition_files_opened=0`;
- `test_used_for_selection=false`;
- `protected_holdout_accessed=false`;
- `automatic_promotion_enabled=false`;
- `execution_enabled=false`;
- `orders_submitted=0`;
- `live_capital_authorized=false`.

### Scientific result

Train:

- support `348`;
- positives `18` (`5.17%`);
- raw AUC `0.998569`;
- raw max probability `0.686309`;
- raw scores `>=0.60`: `5`;
- calibrated scores `>=0.60`: `0`.

Validation:

- support `87`;
- positives `7` (`8.05%`);
- raw AUC `0.811607`;
- raw max probability `0.331543`;
- raw scores `>=0.60`: `0`;
- calibrated scores `>=0.60`: `0`.

Top validation raw-score regions:

- top `10`: `3/10`, empirical `0.30`, Laplace `0.333333`, Wilson lower 95% `0.107791`;
- top `20`: `6/20`, empirical `0.30`, Laplace `0.318182`, Wilson lower 95% `0.145477`;
- top `30`: `6/30`, Laplace `0.21875`;
- top `50`: `6/50`, Laplace `0.134615`.

Calibration:

- persisted calibrated max remains `0.333333333333`;
- best validation calibration bin with support `>=10` has Laplace rate `0.096386`;
- no train/validation region supports a defensible posterior success probability at the frozen `0.60` threshold.

Interpretation:

1. The immediate zero-trade behavior is mechanically caused by the calibration ceiling below `0.60`.
2. The deeper problem is not calibration alone: the model almost perfectly separates train (`AUC≈0.999`) but generalizes materially worse on validation (`AUC≈0.812`) with very sparse positive support. This is evidence of overfit/generalization risk plus insufficient independent positive evidence.
3. The programme should not restart from zero because stable univariate signal exists in several current features, especially `liquidation_burst_intensity`, `volatility_ratio`, and `maximum_event_zscore`.
4. Repeated retraining on the same static sample is not justified. The next scientific route is growth of independent live evidence with controlled retraining.

## Owner decision — production research deployment

The owner explicitly authorizes a follow-up **WH09 Production Research Runtime**.

Important distinction:

- a new operational candidate is **not required** to deploy a production research/shadow runtime;
- a valid candidate **is required** before PAPER/demo position execution or promotion;
- real-money/live-capital execution remains forbidden.

`Production` in this handover means the real production deployment environment and real production market data, not real exchange orders.

### Required follow-up scope

1. Run the WickHunter/Liquid20 live-data collector continuously (`24/7`) using existing production data paths where possible.
2. Run shadow inference on every eligible live decision using the current frozen model/baseline identity for observation only.
3. Persist raw probability, calibrated confidence, final signal/`NO_TRADE`, reason codes, model/parameter identity and relevant market context for every decision.
4. Do not lower or bypass `no_trade_confidence=0.60` to manufacture activity.
5. After the frozen `900 s` horizon, materialize immutable research outcomes/labels, including below-threshold observations, with full provenance and chronological anti-leakage guarantees.
6. Grow an independent chronological research dataset from production evidence.
7. Introduce bounded periodic challenger retraining only after the live collection + provenance + labeling path is proven. A daily cadence is acceptable as an operational trigger, but unchanged data must not be retrained merely to consume compute.
8. Keep scientific selection train/validation-only. Test/protected holdout must not drive feature/model/calibration selection.
9. Extend existing `candidate_paper_runtime_*`, `shadow_runtime_*`, storage/snapshot and `paper_validation.py` components instead of creating a parallel runtime.
10. Expose durable operator telemetry: decision and `NO_TRADE` counts, raw/calibrated confidence distributions, reason codes, model/version/parameter identities, label/outcome statistics, data/model drift and per-symbol/side/regime performance.
11. When an independently defensible candidate exists, permit PAPER/demo comparison and later champion/challenger/baseline operation on the same live market evidence.
12. Retraining and promotion remain separate. No automatic promotion.

### Hard safety boundary

Remain false/zero until a separate explicit authorization changes them:

```yaml
automatic_promotion_enabled: false
trading_credentials_present: false
order_adapter_present: false
execution_enabled: false
orders_submitted: 0
live_capital_authorized: false
```

No real exchange orders. No real capital. PAPER/demo position execution is a later candidate-gated phase.

## Exact continuation sequence for the next agent

1. Read this task record, Issue `#1384` (especially owner handover comment `5226356108`) and PR `#1385` continuation comment `5226357075` before any mutation.
2. Finish discovery PR `#1385`:
   - persist/retain the terminal diagnostic findings;
   - correct the invalid PR title (`research(...)` is rejected by repository Conventional Commit validation; use an allowed type without changing scientific scope);
   - run final exact-head CI;
   - merge/close according to task governance;
   - archive this discovery task as required by `PROMPTING_HANDOVER.md` / task closeout governance.
3. Do **not** rerun H900 and do not lower `no_trade_confidence=0.60`.
4. Create one governed follow-up task/branch/PR named for `WH09_PRODUCTION_RESEARCH_RUNTIME`; avoid duplicate tasks and PR spam.
5. Inventory and reuse existing collector/runtime/storage/telemetry deployment components first; implement only missing seams.
6. Deploy the zero-authority research/shadow runtime to the production environment and prove end-to-end: live data -> inference -> decision journal -> 900 s outcome label -> durable telemetry.
7. Keep the collector running to accumulate independent evidence. Add bounded periodic challenger retraining only after the data/provenance contract is proven.
8. Do not start PAPER/demo position execution until a challenger independently passes the frozen candidate gate.
9. Report accumulating live evidence so the owner/coordinator can deliberately decide when a candidate is ready for PAPER/demo activation.

`NEXT_WORK_PACKAGE: WH09_PRODUCTION_RESEARCH_RUNTIME`

`OWNER_INTENT: deploy now for production-data observation and learning; defer PAPER/demo execution until candidate gate passes; real capital remains out of scope.`

## Context checkpoint

```yaml
phase: handover
session_id: wh09-signal-data-model-20260808-01
session_role: coordinator-investigator
execution_mode: chat_github
decomposition_decision: discovery_first
validation_level: terminal_train_validation_diagnostic
last_completed_step: authoritative diagnostic consumed and owner production-research deployment decision persisted
status: ready_for_closeout
blocker: PR 1385 procedural closeout; its current title uses disallowed type research
next_action: finish PR 1385, archive discovery state, then create and execute one governed WH09 Production Research Runtime follow-up lane
```
