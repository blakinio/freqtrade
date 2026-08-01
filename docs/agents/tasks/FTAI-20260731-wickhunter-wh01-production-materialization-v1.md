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
- PR #899 changed exactly the implementation, focused tests and this task record;
- PR #899 passed exact-head AI Platform CI, full Freqtrade CI including CI Gate and full pre-commit, and security/zizmor;
- PR #899 merged normally as `3afe281de86673902ded7625d6dade94105b5ee9` with zero unresolved threads.

## Production repair checkpoint

- request-only PR #906 independently verified both frozen inputs, all expected hashes and all disabled authority flags on trusted runner `freqtrade-synology-staging`;
- workflow run `30688887667`, job `91339968858`, failed before publication with `Liquid20 import lacks required pre-roll`;
- the accepted import starts about eight hours before the decision interval and fully covers it, while the WH-01 builder requires history strictly before its declared 15-minute burst window rather than a separate 24-hour liquidation interval;
- repair PR #908 aligns the Liquid20 pre-roll bound with the production dataset request's burst window and adds an actual-like regression fixture;
- exact-head `193292a19e8fe902b24d887beaf5031b5c2acf64` passed AI Platform CI `30689330731` and security/zizmor `30689330706`;
- Freqtrade pre-commit job `91341131142` passed mypy and Ruff, then failed only because Ruff format shortened one regression assertion;
- bot commit `a3c641bda235c96b486e200e615247a779b7b77d` applied exactly that formatter diff and removed the temporary workflow;
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
checkpoint_version: 3
updated_at: 2026-08-01T09:18:00+02:00
head: checkpoint commit with parent a3c641bda235c96b486e200e615247a779b7b77d
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
  - repair head a3c641bda235c96b486e200e615247a779b7b77d changes exactly the three owned paths and contains no temporary workflow
  - AI Platform CI 30689330731 and security/zizmor 30689330706 passed on pre-format repair head 193292a19e8fe902b24d887beaf5031b5c2acf64
  - pre-commit job 91341131142 passed mypy and Ruff and requested exactly one Ruff formatter change
  - bot commit a3c641bda235c96b486e200e615247a779b7b77d applied exactly the reported formatter change
 derived:
  - the smallest correct wrapper bound is the declared production burst window; event-level eligibility remains enforced by the unchanged builder
unknown:
  - exact-head CI results for the new user-authored checkpoint head
  - whether the repaired trusted-runner materialization produces non-empty partitions from the frozen real inputs
conflicts: []
first_failure:
  marker: ruff-format modified one regression assertion
  evidence: Freqtrade CI 30689330712 job 91341131142; mypy and Ruff passed before the formatting-only failure
rejected_hypotheses:
  - the frozen Liquid20 package is not corrupt or unverified
  - a new capture or backfill is not required to satisfy the builder's declared 15-minute history boundary
  - the failed attempt did not publish or overwrite an immutable dataset root
  - the exact-head pre-commit failure was not a type, lint or functional defect
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
  - command: AI Platform CI 30689330731
    result: PASS
    evidence: exact pre-format repair head passed tests, compile, Ruff, Ruff format and codespell
  - command: security/zizmor 30689330706
    result: PASS
    evidence: exact pre-format repair head passed security analysis
  - command: Freqtrade pre-commit job 91341131142
    result: FAIL
    evidence: only Ruff format changed one assertion; mypy and Ruff passed
  - command: compare develop...fix/wickhunter-wh01-liquid20-preroll-20260801
    result: PASS
    evidence: behind_by=0 and exactly three owned files; temporary workflows absent
blockers: []
next_action: drive repair PR #908 exact-head AI Platform CI, full Freqtrade CI and security analysis to green, then merge normally
```
