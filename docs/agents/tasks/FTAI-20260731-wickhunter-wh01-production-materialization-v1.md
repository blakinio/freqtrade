# FTAI-20260731-wickhunter-wh01-production-materialization-v1

## Status

`validating`

## Goal

Cryptographically bind the accepted Liquid20 production import to the independently verified Market Evidence v3 package and an explicit purged/embargoed split geometry, then atomically materialize a non-empty WH-01 dataset without protected-holdout access or model authority.

## Frozen production inputs

- Market Evidence run: `wickhunter-production-market-evidence-20260731-v3-r1`;
- Market Evidence manifest: `eaccc5ecaf7a9514086e99d719d0cb4c5ef8a9c87e3f0c30c501e1860c05fb52`;
- accepted Liquid20 operation: `wickhunter-production-live-archive-20260731-v1`;
- accepted import run: `first-party-live:liquid20-20260731T000000Z-0:b9617c6006b6c4b9`;
- Liquid20 selection: `8f5be573684e97140fdccb6f3228166e4c9e5165e89f0f530fe842bb1bedb0fd`;
- protected holdout begins: `1785542400000`.

## Owned paths

- `ai_platform/wickhunter/production_dataset_materialization.py`;
- `tests/ai_platform_integration/test_wickhunter_production_dataset_materialization.py`;
- this task record.

## Required behavior

1. Verify the complete immutable Market Evidence package and accepted Liquid20 import before use.
2. Derive availability-safe market contexts from completed Binance candles and source-separated quality records; each decision timestamp must be at least the latest availability timestamp of all evidence used.
3. Derive dynamic-universe snapshots from observed source health, market availability and completed-candle coverage rather than admitting symbols by configuration alone.
4. Freeze ordered train/validation/test windows with purge/embargo gaps and no protected-holdout overlap.
5. Call the existing WH-01 builder without weakening its accepted-import, availability-time, split or no-overwrite contracts.
6. Publish an atomic materialization containing a self-hashed source binding, non-empty dataset manifest, partition hashes, checksum index and independent verification report.
7. Bind Market Evidence manifest/binding/lineage hashes, Liquid20 selection hash, split geometry hash, dataset request hash, exact code SHA and dataset manifest hash.
8. Keep credentials, replay, execution, model execution, live capital and orders disabled.

## Validation checkpoint

- focused functional tests passed on the initial implementation head;
- all reported Ruff/import/format findings were repaired mechanically;
- the one-shot autofix removed itself from the branch;
- the full `mypy --all-files` hook passed after disambiguating the materialization tuple keys;
- the current PR changes exactly the implementation, focused tests and this task record;
- regular exact-head workflows on bot-authored head `e985cb1ca5d180fab11cea9173ef8c5adfa1ed75` were `action_required` without jobs, so this meaningful checkpoint records the completed mypy repair and triggers normal exact-head CI.

## Production repair checkpoint

- request-only PR #906 independently verified both frozen inputs, all expected hashes and all disabled authority flags on trusted runner `freqtrade-synology-staging`;
- workflow run `30688887667`, job `91339968858`, failed before publication with `Liquid20 import lacks required pre-roll`;
- the accepted import starts about eight hours before the decision interval and fully covers it, while the WH-01 builder requires history strictly before its declared 15-minute burst window rather than a separate 24-hour liquidation interval;
- this repair aligns the Liquid20 pre-roll bound with the production dataset request's burst window and keeps the builder's actual event-history eligibility checks unchanged;
- no capture, backfill, holdout access, synthetic data, replay, model execution, trading credentials, orders or live capital were used.

## Acceptance

- focused tests cover split geometry, availability-safe input derivation, source binding and tamper rejection;
- exact-head AI Platform CI, full Freqtrade CI and security analysis are green;
- implementation merges normally before the trusted-runner materialization request;
- the real materialization produces at least one partition and row;
- final verification reports `wh01_ready=true`, `wh01_blocker=null`, `protected_holdout_accessed=false`, `model_execution_authorized=false` and `orders_submitted=0`.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-08-01T08:36:00+02:00
head: checkpoint commit with parent e985cb1ca5d180fab11cea9173ef8c5adfa1ed75
branch: agent/wickhunter-wh01-production-materialization
pr: "#899"
status: validating
context_routes:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/tasks/FTAI-20260731-wickhunter-wh01-production-materialization-v1.md
  - ai_platform/wickhunter/production_dataset_materialization.py
  - tests/ai_platform_integration/test_wickhunter_production_dataset_materialization.py
owned_paths:
  - ai_platform/wickhunter/production_dataset_materialization.py
  - tests/ai_platform_integration/test_wickhunter_production_dataset_materialization.py
  - docs/agents/tasks/FTAI-20260731-wickhunter-wh01-production-materialization-v1.md
proven:
  - develop remains 55b63820f50976e3fcf605f1cea0810183d2b842 and PR #899 is behind_by=0
  - PR #899 changes exactly the three owned paths
  - full mypy --all-files passed after source_key and quality_key disambiguation
  - temporary autofix and mypy one-shot workflows are absent from the final diff
  - regular workflows on e985cb1ca5d180fab11cea9173ef8c5adfa1ed75 ended action_required without jobs
  - the only unresolved review thread is outdated and targets the removed mypy one-shot workflow
derived:
  - a normal user-authored checkpoint commit is required to obtain runnable exact-head CI
unknown:
  - exact results of the new AI Platform CI, Freqtrade CI, pre-commit and security runs
conflicts: []
first_failure:
  marker: action_required
  evidence: workflow runs 30687914521, 30687914519, 30687914516 and 30687914518 created no jobs on the bot-authored head
rejected_hypotheses:
  - action_required is not evidence of an implementation failure because no jobs ran
changed_paths:
  - docs/agents/tasks/FTAI-20260731-wickhunter-wh01-production-materialization-v1.md
validation:
  - command: compare develop...agent/wickhunter-wh01-production-materialization
    result: PASS
    evidence: ahead_by=10 behind_by=0 and exactly three owned files
  - command: list PR #899 review threads
    result: FAIL
    evidence: one outdated unresolved zizmor thread remains for a deleted workflow
  - command: fetch exact-head workflow runs for e985cb1ca5d180fab11cea9173ef8c5adfa1ed75
    result: BLOCKED
    evidence: four regular workflows concluded action_required without jobs
blockers: []
next_action: verify the new checkpoint head, resolve the outdated review thread, and drive all exact-head workflows to green
```
