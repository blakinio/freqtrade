---
task_id: FTAI-20260725-rl-v2-lifecycle-attribution-interpretation
status: active
branch: docs/rl-v2-lifecycle-attribution-interpretation-20260725
base_branch: develop
created: 2026-07-25
updated: 2026-07-25
related_pr: "TBD"
owned_paths:
  - docs/agents/tasks/FTAI-20260725-rl-v2-lifecycle-attribution-interpretation.md
  - docs/ai_platform/RL_V2_LIFECYCLE_ATTRIBUTION_INTERPRETATION.md
  - ai_platform/experimental_model_research/rl-v2-lifecycle-attribution-interpretation-v1.json
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/ai_platform/ARCHITECTURE.md
  - docs/ai_platform/ROADMAP.md
  - docs/agents/tasks/FTAI-20260724-rl-v2-historical-evidence-diagnosis.md
  - docs/agents/tasks/FTAI-20260724-rl-v2-roi-lifecycle-alignment.md
  - docs/agents/tasks/FTAI-20260724-rl-v2-roi-lifecycle-paired-attribution-execution.md
search_first:
  - current develop and open PRs overlapping RL-v2 interpretation, reward, lifecycle, evaluation or holdout work
---

# RL-v2 Lifecycle Attribution Interpretation

## Goal

Interpret the immutable paired historical-development evidence from workflow run `30131273189` without
executing a model, accessing market data, rerunning the baseline, retuning frozen inputs, or converting
the result into selection or promotion evidence.

The task must determine whether the zero targeted external-exit churn is a genuine lifecycle result or a
degenerate zero-trade/disabled-exit artifact, document remaining uncertainty, and freeze the next-action
boundary.

## Source boundary

The only result source is immutable artifact
`rl-v2-roi-lifecycle-paired-attribution-272` with digest
`sha256:11e9d9a8e5f8e65474406524445c7b04fe3d9af5afa6d137847c913f8e66ae04`.

The artifact remains:

- `paired_historical_development_attribution`;
- `strict_oos=false`;
- `protected_final_validation=false`;
- `consumed_historical_oos_accessed=false`;
- `protected_final_holdout_accessed=false`.

## Allowed scope

- Inspect provenance, config, metadata, coverage, and raw recorded trades from the immutable artifact.
- Recalculate deterministic gross-price PnL, fees, net PnL, pair/month/exit-reason and duration summaries.
- Inspect same-pair re-entry intervals and position exposure from recorded trades.
- Determine whether the targeted mechanism result is non-degenerate.
- Record a bounded interpretation and future no-execution policy.

## Non-negotiable boundaries

- No training, backtest, market-data access, or baseline rerun.
- No PPO, reward, feature, threshold, ROI, stop-loss, pair, timeframe, fee, or action-semantics mutation.
- No use of consumed OOS `20260501-20260630`.
- No access to protected final holdout `20260801-20260930`.
- No strict-OOS, final-validation, ranking, promotion, profitability, superiority, dry-run, or live claim.
- Frozen thresholds `0.006/-0.009` remain unchanged.
- Phase 6 authoritative `selected_model=null` remains unchanged.
- This interpretation cannot itself authorize another experiment.

## Result

The analysis is recorded in:

- `docs/ai_platform/RL_V2_LIFECYCLE_ATTRIBUTION_INTERPRETATION.md`;
- `ai_platform/experimental_model_research/rl-v2-lifecycle-attribution-interpretation-v1.json`.

The targeted inherited external ROI/stop-loss immediate re-entry mechanism is resolved in the reused
historical-development window. The result is non-degenerate because 45 trades executed across both
pairs, exposure remained nearly continuous, and target-flat, ROI, stop-loss, and force-exit paths all
remained active.

Aggregate profitability is not robust evidence: BTC remained negative, March remained negative, only 14
of 45 trades won net, the median trade was negative, and a few large winners dominated the total result.
Eight target-flat exits still had one-candle same-pair re-entry, but that separate policy transition does
not authorize retuning on the reused evidence window.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-25T09:56:00+02:00
head: 98e8857a183f4603a9abc1cb466e8897eb589334
branch: docs/rl-v2-lifecycle-attribution-interpretation-20260725
pr: null
status: active
context_routes:
  - docs/agents/tasks/FTAI-20260724-rl-v2-historical-evidence-diagnosis.md
  - docs/agents/tasks/FTAI-20260724-rl-v2-roi-lifecycle-alignment.md
  - docs/agents/tasks/FTAI-20260724-rl-v2-roi-lifecycle-paired-attribution-execution.md
owned_paths:
  - docs/agents/tasks/FTAI-20260725-rl-v2-lifecycle-attribution-interpretation.md
  - docs/ai_platform/RL_V2_LIFECYCLE_ATTRIBUTION_INTERPRETATION.md
  - ai_platform/experimental_model_research/rl-v2-lifecycle-attribution-interpretation-v1.json
proven:
  - The only analyzed result is immutable artifact rl-v2-roi-lifecycle-paired-attribution-272 from run 30131273189, digest sha256:11e9d9a8e5f8e65474406524445c7b04fe3d9af5afa6d137847c913f8e66ae04.
  - The downloaded ZIP digest and all hash-bound payload identities reconcile with the completed execution checkpoint.
  - No new training, backtest, market-data access, baseline rerun, retuning, ranking, promotion, OOS access or holdout access occurred.
  - The 45 trades reconcile to gross price PnL +29.866574 USDT, fees 18.059698 USDT and net PnL +11.806876 USDT.
  - The targeted metrics remain zero versus baseline 122 ROI 15-minute re-entries, 131 immediate external boundaries and 52.582123 USDT boundary fees.
  - Both ROI exits had next same-pair entries after 45 minutes and the one stop-loss exit after 135 minutes.
  - Both pairs traded; BTC exposure was 96.23 percent, ETH exposure 98.67 percent and both positions were concurrently active for 95.95 percent of the interval.
  - Target-flat, ROI, hard stop-loss and terminal force-exit paths all remained active, so the zero targeted churn result is non-degenerate.
  - BTC net PnL was -1.264043 USDT while ETH net PnL was +13.070919 USDT; March was -8.340107 USDT and April +22.981776 USDT.
  - Only 14 of 45 trades were net winners, median trade PnL was -0.866404 USDT and the three largest winners exceeded the total net result.
  - Eight target-flat exits were followed by same-pair re-entry after 15 minutes; this remains a separate policy-level observation.
  - Phase 6 selected_model remains null and the evidence remains paired historical-development attribution only.
derived:
  - The prospectively selected lifecycle flag resolved the diagnosed inherited external ROI/stop-loss immediate re-entry mechanism in this reused window.
  - The variant did not establish cross-pair, cross-month, statistical or strict-OOS profitability robustness.
  - Target-flat transition quality cannot be causally inferred from this run because lifecycle alignment changed the full exposure and trade path.
unknown:
  - PPO stability across seeds and fresh prospective windows remains unknown.
  - Future behavior outside the reused March-April development window remains unknown.
conflicts: []
first_failure:
  marker: RESOLVED_TARGETED_MECHANISM_ONLY
  evidence: The variant removed all prospectively frozen immediate external ROI/stop-loss re-entry boundaries while preserving active trading and exit paths.
rejected_hypotheses:
  - Treat zero targeted churn as a zero-trade or globally disabled-exit artifact.
  - Treat positive aggregate net PnL as strict-OOS profitability, superiority or promotion evidence.
  - Retune target-flat behavior, PPO, reward, features, thresholds or action semantics on the reused window.
  - Rerun the immutable baseline or any trigger PR.
  - Access consumed historical OOS or the protected final holdout.
changed_paths:
  - docs/agents/tasks/FTAI-20260725-rl-v2-lifecycle-attribution-interpretation.md
  - docs/ai_platform/RL_V2_LIFECYCLE_ATTRIBUTION_INTERPRETATION.md
  - ai_platform/experimental_model_research/rl-v2-lifecycle-attribution-interpretation-v1.json
validation:
  - command: immutable artifact digest and payload identity verification
    result: PASS
    evidence: ZIP digest and individual source-file SHA-256 values match the recorded artifact and generated interpretation bindings.
  - command: deterministic recorded-trade accounting and lifecycle decomposition
    result: PASS
    evidence: Gross price PnL, fees, net PnL, pair/month/exit summaries, durations, exposure and re-entry intervals reconcile from the raw 45 trades.
  - command: JSON syntax validation
    result: PASS
    evidence: python -m json.tool accepts the machine-readable interpretation descriptor.
blockers: []
next_action: Pause RL-v2 experimentation; any future evaluation must be a separate prospectively declared task with frozen inputs and a fresh non-contaminated window, and this task does not authorize that execution.
```
