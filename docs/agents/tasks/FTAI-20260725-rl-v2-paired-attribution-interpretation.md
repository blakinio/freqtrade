---
task_id: FTAI-20260725-rl-v2-paired-attribution-interpretation
status: done
branch: develop
base_branch: develop
created: 2026-07-25
updated: 2026-07-25
related_pr: "274"
owned_paths:
  - docs/agents/tasks/FTAI-20260725-rl-v2-paired-attribution-interpretation.md
  - docs/ai_platform/RL_V2_PAIRED_ATTRIBUTION_INTERPRETATION.md
  - ai_platform/experimental_model_research/rl-v2-paired-attribution-interpretation-v1.json
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/tasks/FTAI-20260724-rl-v2-roi-lifecycle-paired-attribution-execution.md
  - docs/ai_platform/RL_V2_HISTORICAL_EVIDENCE_DIAGNOSIS.md
  - docs/ai_platform/RL_V2_ROI_LIFECYCLE_ALIGNMENT.md
  - docs/ai_platform/ROADMAP.md
search_first:
  - current develop and open PRs overlapping RL-v2 interpretation, model selection, Phase 6 or experimental research ownership
optional_reads:
  - docs/ai_platform/ARCHITECTURE.md
---

# RL-v2 Paired Attribution Interpretation

## Goal

Interpret the immutable lifecycle paired-attribution evidence without executing any model, backtest,
market-data operation or baseline rerun. Persist the exact evidentiary boundary, distinguish mechanistic
support from profitability and generalization, and identify the next legal research gate.

## Source evidence

- completed task `FTAI-20260724-rl-v2-roi-lifecycle-paired-attribution-execution`;
- workflow run `30131273189`;
- execution head `ce83a3e52ab6bc8676072522e266dcf50bd692e7`;
- artifact `rl-v2-roi-lifecycle-paired-attribution-272`;
- artifact digest `sha256:11e9d9a8e5f8e65474406524445c7b04fe3d9af5afa6d137847c913f8e66ae04`;
- classification `paired_historical_development_attribution`;
- `strict_oos=false`, `protected_final_validation=false`.

## Non-negotiable boundaries

- No training, backtest, data download, cache restore or exchange access.
- No baseline rerun.
- No consumed historical OOS `20260501-20260630`.
- No protected final holdout `20260801-20260930`.
- No PPO, reward, feature, model, strategy, threshold, pair, timeframe, fee or geometry change.
- No profitability, superiority, ranking, promotion, dry-run or live-readiness claim.
- Phase 6 remains complete with authoritative `selected_model=null`.

## Deliverables

- a human-readable interpretation report;
- a machine-readable interpretation record bound to immutable source digests;
- one prospectively bounded recommendation for the next research declaration, without authorizing its
  execution.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-25T10:05:00+02:00
head: 69e2880f8e7fc916c89032eec473b6ef9941e9ea
branch: develop
pr: 274
status: done
context_routes:
  - docs/agents/tasks/FTAI-20260724-rl-v2-roi-lifecycle-paired-attribution-execution.md
  - docs/ai_platform/RL_V2_HISTORICAL_EVIDENCE_DIAGNOSIS.md
  - docs/ai_platform/RL_V2_ROI_LIFECYCLE_ALIGNMENT.md
owned_paths:
  - docs/agents/tasks/FTAI-20260725-rl-v2-paired-attribution-interpretation.md
  - docs/ai_platform/RL_V2_PAIRED_ATTRIBUTION_INTERPRETATION.md
  - ai_platform/experimental_model_research/rl-v2-paired-attribution-interpretation-v1.json
proven:
  - PR 274 merged the interpretation task, report and machine-readable record to develop as 69e2880f8e7fc916c89032eec473b6ef9941e9ea.
  - AI Platform CI 1156, Freqtrade CI 1351 and zizmor 1281 passed on the final PR 274 head c06c7efa765e8a0be78fb67b553c71efb1e94b65.
  - Immutable artifact rl-v2-roi-lifecycle-paired-attribution-272 remains bound to run 30131273189, execution head ce83a3e52ab6bc8676072522e266dcf50bd692e7 and digest sha256:11e9d9a8e5f8e65474406524445c7b04fe3d9af5afa6d137847c913f8e66ae04.
  - The downloaded artifact ZIP digest and hash-bound source payload identities reconcile with the completed execution checkpoint.
  - Run 30131273189 executed exactly one lifecycle-aligned variant backtest, no baseline command, no consumed historical OOS and no protected final holdout access.
  - The interpretation task executed no model, backtest, market-data operation, cache restore, baseline rerun, retuning, ranking or promotion.
  - Prospectively frozen metrics passed: ROI-to-15m re-entry count 122 to 0, immediate external boundaries 131 to 0 and boundary fees 52.582123 USDT to 0.0 USDT.
  - The 45 variant trades reconcile to gross price PnL +29.866574 USDT, fees 18.059698 USDT and net PnL +11.806876 USDT.
  - The zero targeted churn result is non-degenerate: both pairs traded, BTC exposure was 96.23 percent, ETH exposure 98.67 percent and both positions were concurrently active for 95.95 percent of the interval.
  - Target-flat, ROI, hard stop-loss and terminal force-exit paths remained active; both ROI exits re-entered after 45 minutes and the stop-loss exit after 135 minutes rather than 15 minutes.
  - Profitability is concentrated and non-gating: BTC was -1.264043 USDT, ETH +13.070919 USDT, March -8.340107 USDT, April +22.981776 USDT and the median trade -0.866404 USDT.
  - Eight target-flat exits still had same-pair re-entry after one 15-minute candle; this is a separate policy-level observation and not authorization for same-window retuning.
  - Parallel PR 275 was closed without merge after PR 274 became the canonical source, preventing duplicate task, report and descriptor records.
  - Evidence remains paired_historical_development_attribution with strict_oos=false, protected_final_validation=false, profitability non-gating and Phase 6 selected_model=null.
derived:
  - The single lifecycle delta resolved the defined inherited external ROI/stop-loss immediate re-entry mechanism on the reused March-April development path.
  - The mechanism result is not explained by zero trading or globally disabled exits.
  - Positive aggregate PnL does not establish cross-pair, cross-month, statistical or strict-OOS robustness.
  - Target-flat behavior cannot be causally judged from this run because lifecycle alignment changed the complete exposure and trade path.
unknown:
  - Whether the mechanism result is stable across prospectively frozen PPO seeds.
  - Whether any result generalizes to a fresh untouched evidence window.
conflicts: []
first_failure:
  marker: NONE
  evidence: Interpretation and closure used immutable evidence only; duplicate ownership was resolved by closing PR 275 without merge.
rejected_hypotheses:
  - Treat the paired result as strict OOS or final validation.
  - Treat zero targeted churn as a zero-trade or globally disabled-exit artifact.
  - Attribute the full profit delta causally to removed boundary fees.
  - Retune target-flat behavior, PPO, reward, features, thresholds or action semantics on the reused window.
  - Reopen or rerun the immutable baseline or any trigger PR.
  - Rank RL-v2 against PyTorch or completed Phase 6 models.
  - Use consumed OOS or protected final holdout for iterative research.
changed_paths:
  - docs/agents/tasks/FTAI-20260725-rl-v2-paired-attribution-interpretation.md
  - docs/ai_platform/RL_V2_PAIRED_ATTRIBUTION_INTERPRETATION.md
  - ai_platform/experimental_model_research/rl-v2-paired-attribution-interpretation-v1.json
validation:
  - command: immutable artifact digest and payload identity verification
    result: PASS
    evidence: ZIP digest and individual source payload SHA-256 values reconcile with the recorded artifact identity.
  - command: deterministic raw-trade accounting and lifecycle audit
    result: PASS
    evidence: Gross PnL, fees, net PnL, pair and month concentration, exposure, exit paths, durations and re-entry intervals reconcile from all 45 recorded trades.
  - command: standard PR 274 CI
    result: PASS
    evidence: AI Platform CI 1156, Freqtrade CI 1351 and zizmor 1281 completed successfully.
  - command: merge PR 274 and close duplicate PR 275 without merge
    result: PASS
    evidence: GitHub records canonical interpretation merge 69e2880f8e7fc916c89032eec473b6ef9941e9ea and duplicate PR 275 closed with merged=false.
blockers: []
next_action: Do not execute seed-robustness work from this completed task; declare a separate prospectively bounded task only if pursued, freezing seeds and all model, strategy, reward, feature, threshold, pair, timeframe, fee and geometry inputs while forbidding baseline rerun, consumed OOS, protected holdout, ranking, promotion and deployment claims.
```
