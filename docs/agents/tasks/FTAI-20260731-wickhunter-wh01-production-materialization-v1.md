# FTAI-20260731-wickhunter-wh01-production-materialization-v1

## Status

`completed`

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
- PR #899 changed exactly the implementation, focused tests and this task record;
- PR #899 passed exact-head AI Platform CI, full Freqtrade CI including CI Gate and full pre-commit, and security/zizmor;
- PR #899 merged normally as `3afe281de86673902ded7625d6dade94105b5ee9` with zero unresolved threads.

## Production repair checkpoint

- request-only PR #906 independently verified both frozen inputs, all expected hashes and all disabled authority flags on trusted runner `freqtrade-synology-staging`;
- workflow run `30688887667`, job `91339968858`, failed before publication with `Liquid20 import lacks required pre-roll`;
- the accepted import starts about eight hours before the decision interval and fully covers it, while the WH-01 builder requires history strictly before its declared 15-minute burst window rather than a separate 24-hour liquidation interval;
- repair PR #908 aligns the Liquid20 pre-roll bound with the production dataset request's burst window and adds an actual-like regression fixture;
- exact-head `8c43e24f7ddc0cf41584b8caec60d7b979fc78b2` passed AI Platform CI `30689504518`, full Freqtrade CI `30689504493` including CI Gate and full pre-commit, and security/zizmor `30689504496`;
- `develop` then advanced by 49 commits; it was merged normally into the repair branch without force-push or conflict;
- synced bot head `49e422eae3c73bb8da6192e47d83990e58a386fb` is based on `develop` `343bd2eda79045d7bbd6c86c2b4aa68bb8030025` and the temporary sync workflow is absent;
- the final diff again contains only the implementation, focused test and this task record;
- no capture, backfill, holdout access, synthetic data, replay, model execution, trading credentials, orders or live capital were used.

## Acceptance

- focused tests cover split geometry, availability-safe input derivation, source binding and tamper rejection;
- exact-head AI Platform CI, full Freqtrade CI and security analysis are green;
- implementation merges normally before the trusted-runner materialization request;
- the real materialization produces at least one partition and row;
- final verification reports `wh01_ready=true`, `wh01_blocker=null`, `protected_holdout_accessed=false`, `model_execution_authorized=false` and `orders_submitted=0`.

## Context checkpoint

```yaml
checkpoint_version: 4
updated_at: 2026-08-01T09:38:00+02:00
head: checkpoint commit with parent 49e422eae3c73bb8da6192e47d83990e58a386fb
branch: fix/wickhunter-wh01-liquid20-preroll-20260801
pr: "#908"
status: validating
context_routes:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/tasks/FTAI-20260731-wickhunter-wh01-production-materialization-v1.md
  - ai_platform/wickhunter/production_dataset_materialization.py
  - ai_platform/wickhunter/dataset.py
  - tests/ai_platform_integration/test_wickhunter_production_dataset_materialization.py
owned_paths:
  - ai_platform/wickhunter/production_dataset_materialization.py
  - tests/ai_platform_integration/test_wickhunter_production_dataset_materialization.py
  - docs/agents/tasks/FTAI-20260731-wickhunter-wh01-production-materialization-v1.md
proven:
  - PR #899 merged normally as 3afe281de86673902ded7625d6dade94105b5ee9 after green exact-head CI and zero unresolved threads
  - request-only PR #906 verified both frozen packages and all expected hashes before failing at the wrapper pre-roll check
  - PR #906 was closed without merge after terminal failure evidence was recorded
  - accepted Liquid20 requested_start_ms is 1785456000629, about eight hours before decision_start_ms 1785484800000
  - accepted Liquid20 requested_end_ms 1785534275466 covers decision_end_ms 1785520800000 and remains before holdout 1785542400000
  - WH-01 dataset history is defined strictly before decision_timestamp_ms minus burst_window_ms
  - production burst_window_ms is 900000 and minimum_history_events is 1
  - the hard-coded 86400000-millisecond Liquid20 wrapper pre-roll was not a dataset-builder requirement
  - repair head 8c43e24f7ddc0cf41584b8caec60d7b979fc78b2 passed AI Platform CI 30689504518, Freqtrade CI 30689504493 and security/zizmor 30689504496
  - current develop 343bd2eda79045d7bbd6c86c2b4aa68bb8030025 was merged normally into the repair branch
  - synced head 49e422eae3c73bb8da6192e47d83990e58a386fb changes exactly the three owned paths and contains no temporary workflow
derived:
  - the smallest correct wrapper bound is the declared production burst window; event-level eligibility remains enforced by the unchanged builder
unknown:
  - exact-head CI results for the post-sync user-authored checkpoint head
  - whether the repaired trusted-runner materialization produces non-empty partitions from the frozen real inputs
conflicts: []
first_failure:
  marker: develop advanced after a green exact-head run
  evidence: compare showed behind_by=49 after CI 30689504493 completed successfully
rejected_hypotheses:
  - the frozen Liquid20 package is not corrupt or unverified
  - a new capture or backfill is not required to satisfy the builder's declared 15-minute history boundary
  - the failed attempt did not publish or overwrite an immutable dataset root
  - the branch did not require force-push or conflict resolution to absorb current develop
changed_paths:
  - ai_platform/wickhunter/production_dataset_materialization.py
  - tests/ai_platform_integration/test_wickhunter_production_dataset_materialization.py
  - docs/agents/tasks/FTAI-20260731-wickhunter-wh01-production-materialization-v1.md
validation:
  - command: trusted-runner source verification in workflow 30688887667
    result: PASS
    evidence: Market Evidence manifest/binding/lineage and accepted Liquid20 selection hashes matched frozen values
  - command: trusted-runner materialization in workflow 30688887667
    result: FAIL
    evidence: first failure was the hard-coded 24-hour Liquid20 pre-roll wrapper check
  - command: AI Platform CI 30689504518
    result: PASS
    evidence: repair head passed tests, compile, Ruff, Ruff format and codespell
  - command: Freqtrade CI 30689504493
    result: PASS
    evidence: full pre-commit, documentation, Core matrix, coverage, distributions and CI Gate passed
  - command: security/zizmor 30689504496
    result: PASS
    evidence: repair head passed security analysis
  - command: merge current develop into repair branch
    result: PASS
    evidence: synced head 49e422eae3c73bb8da6192e47d83990e58a386fb, no conflict, no force-push, temporary workflow absent
  - command: compare develop...fix/wickhunter-wh01-liquid20-preroll-20260801
    result: PASS
    evidence: behind_by=0 and exactly three owned files after sync
blockers: []
next_action: drive post-sync exact-head AI Platform CI, full Freqtrade CI and security analysis to green, then merge PR #908 normally
```

## Production metric-binding repair checkpoint

- request-only PR #911 reverified the frozen Market Evidence v3 and accepted Liquid20 packages, then failed before dataset publication because the generated market snapshots lacked the nine canonical WH-00/WH-01 metric names;
- request-only observer PR #912 confirmed the exact production candle, market-quality, source-health and accepted Liquid20 schemas and closed without merge;
- the repair reuses the existing production WH-01 candle formulas and frozen 24-hour lookbacks, derives source-balanced spread from every verified source, and derives market-wide liquidation intensity from complete prior accepted-import burst buckets;
- the metric policy is self-hashed and bound into both the source binding and materialization manifest;
- no capture, backfill, synthetic production observation, protected-holdout access, replay, model execution, trading credential, order or live capital is introduced.


## Terminal production materialization checkpoint

- canonical metric-binding repair PR #914 passed exact-head AI Platform CI `30692428808`, full Freqtrade CI `30692428826` including CI Gate, and security/zizmor `30692428833` on head `4d9077255753d626058161fa0a71094ed8bc9cd1`;
- PR #914 changed exactly the implementation, focused regression test and this task record, had zero review threads, and merged normally as `2091971608df3c33238c845f5f019a384b231580`;
- request-only PR #921 added exactly one workflow relative to that merged code SHA and closed without merge after terminal success;
- trusted-runner workflow `30693346424`, job `91351904433`, completed successfully on `freqtrade-synology-staging`;
- immutable dataset: `wickhunter-wh01-production-dataset-20260731-v3-2091971608df-eaccc5ec-8f5be573`;
- immutable root: `/var/lib/freqtrade-staging-state/wickhunter-production-datasets/wickhunter-wh01-production-dataset-20260731-v3-2091971608df-eaccc5ec-8f5be573`;
- dataset manifest SHA-256: `3b0a052d13c8d3684a9bf63712ee00d5a9c09343d14e628c6611a444024b2d51`;
- dataset manifest file SHA-256: `dfddc58ffc7e768d53883bea85dbb860cb0397f3d6995d600c2540530d274bae`;
- dataset request SHA-256: `fbeb64bd364e13c114e15865775fbd1df2c96160e5825f186152c8b611a3716e`;
- source binding SHA-256: `9d4f30c61a9810250ff8786cca69e916e4fe19d8cdfe5d20483150af0ed159bd`;
- materialization SHA-256: `ee4588d56918a79a690ffad965ab4e13014bfd79656880ad4c71bc728c468778`;
- split geometry SHA-256: `cb861e99fc7d2d9b9fd22aa86d4e890595d2765445c5a46b0d0911104ef7cc8b`;
- 154 immutable partitions and 919 rows were independently verified;
- decision range is `1785484861174..1785520559257`;
- ordered train/validation/test windows retain two explicit 30-minute embargo gaps and end before protected holdout `1785542400000`;
- `wh01_ready=true`, `wh01_blocker=null`, `protected_holdout_accessed=false`, `immutable_inputs_mutated=false`, `model_execution_authorized=false`, `replay_authorized=false`, `performance_research_authorized=false`, `execution_enabled=false`, `live_capital_authorized=false`, `trading_credentials_present=false`, `orders_submitted=0`;
- bounded metadata artifact `8816466252` has digest `sha256:816e5b11f9d3c3d3098509d0181b5aff11053cb461c77675ad108af7a0cb1c94` and expires on 2026-08-31;
- Portal runtime/observability is not claimed by this package: WH-08 remains separately gated by WH-07;
- WH-02 is unblocked only at its real accepted immutable dataset dependency and remains `not_started` until a separate governed replay package is opened.

```yaml
checkpoint_version: 6
updated_at: 2026-08-01T11:20:00+02:00
status: completed
implementation_merge: 2091971608df3c33238c845f5f019a384b231580
request_pr: "#921"
request_merged: false
workflow_run: 30693346424
workflow_job: 91351904433
dataset_id: wickhunter-wh01-production-dataset-20260731-v3-2091971608df-eaccc5ec-8f5be573
dataset_manifest_sha256: 3b0a052d13c8d3684a9bf63712ee00d5a9c09343d14e628c6611a444024b2d51
partition_count: 154
total_rows: 919
wh01_ready: true
wh01_blocker: null
protected_holdout_accessed: false
model_execution_authorized: false
replay_authorized: false
performance_research_authorized: false
execution_enabled: false
live_capital_authorized: false
trading_credentials_present: false
orders_submitted: 0
blockers: []
next_action: create a fresh WH-02 deterministic replay and event-label task from current develop, binding this exact immutable dataset without touching the protected final holdout
```
