---
task_id: FTAI-20260801-wickhunter-wh02-replay-price-path-v1
status: validating
branch: feat/wickhunter-wh02-replay-price-path-v1
base_branch: develop
created: 2026-08-01
updated: 2026-08-01
related_pr: null
depends_on:
  - FTAI-20260731-wickhunter-wh01-production-materialization-v1
owned_paths:
  - ai_platform/wickhunter/replay_price_path.py
  - tests/ai_platform_integration/test_wickhunter_replay_price_path.py
  - docs/ai_platform/WICKHUNTER_REPLAY_PRICE_PATH.md
  - docs/agents/tasks/FTAI-20260801-wickhunter-wh02-replay-price-path-v1.md
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/programs/FTAI_WICKHUNTER_LIQUIDATION_BOT_PROGRAM.md
  - docs/agents/tasks/FTAI-20260731-wickhunter-wh01-production-materialization-v1.md
  - docs/ai_platform/WICKHUNTER_DATASET_BUILDER.md
  - docs/ai_platform/WICKHUNTER_REPLAY_PRICE_PATH.md
search_first:
  - current develop HEAD, open PRs and overlapping WickHunter, Market Evidence, Liquid20, replay, strategy and Portal ownership
  - existing dataset, canonical identity, atomic publication and historical source-import contracts
optional_reads: []
---

# WickHunter WH-02 exact replay price-path source

## Goal

Remove the first truthful WH-02 blocker without generating labels or strategy results:

```text
verified immutable WH-01 dataset
  + official public Binance USD-M daily aggTrades archives/checksums
  -> deterministic exact trade sequence per dataset symbol
  -> exact decision/horizon coverage evidence
  -> atomic immutable replay price-path package
```

## Proven blocker

Request-only observer PR #925 completed on trusted runner `freqtrade-synology-staging` in workflow `30694020763`, job `91353627926`.

It inspected the exact production dataset manifest `3b0a052d13c8d3684a9bf63712ee00d5a9c09343d14e628c6611a444024b2d51` and proved:

- all 919 decision timestamps occur inside an already-open 5-minute candle;
- no decision is candle-aligned;
- decision offsets range from 2,876 ms to 65,002 ms across 108 distinct offsets;
- only zero to two fully post-decision 5-minute bars fit inside the declared 15-minute horizon;
- all 919 rows lack an exact complete post-decision 15-minute price path;
- all 919 reversal and all 919 continuation evaluations under the current compatibility prior return `ignore`;
- exact entry, TP-before-SL ordering, MFE, MAE and time-to-outcome cannot be derived truthfully from the 5-minute package;
- terminal blocker: `BLOCKED_EXACT_REPLAY_PRICE_PATH_ABSENT`;
- metadata artifact `8816635402`, digest `sha256:72ecf117cb9f0f1fd776174f170e6fcf288ee7bfdf422bbbaf2852458fa22653`.

PR #925 was closed without merge. No label, replay result or performance claim was produced.

## Scope

This package delivers a local, network-free importer and verifier for official public Binance USD-M daily `aggTrades` ZIP/CHECKSUM pairs:

- strict immutable request contract bound to exact WH-01 and Market Evidence identities;
- confined path and symlink checks;
- official checksum verification before ZIP parsing;
- safe single-member ZIP handling with bounded size/ratio;
- exact seven-column aggregate-trade parsing with optional recognized header;
- positive decimal price/quantity and valid trade/timestamp/side contracts;
- strict deterministic timestamp/aggregate-ID ordering;
- independent verification of WH-01 materialization, partitions and row hashes;
- exact dataset symbol and decision/horizon coverage;
- canonical per-trade and per-partition hashes;
- self-hashed manifest, complete checksum index and atomic no-overwrite publication;
- focused synthetic regression tests.

## Out of scope

- network download or provider polling in the core importer;
- source credentials, proxy routing or private endpoints;
- labels, TP/SL ordering, replay, costs, slippage, MFE, MAE or time-to-outcome;
- changing strategy parameters to manufacture candidates;
- model fitting, optimization, performance research or profitability claims;
- protected final holdout access;
- Portal, order, execution or live-capital authority.

## Source contract

The official Binance public-data documentation states that USD-M futures `aggTrades` correspond to `/fapi/v1/aggTrades`, daily files are published after the source day and every ZIP has a `.CHECKSUM` file.

The later operational request must use exact public paths for `2026-07-31` and the exact symbols present in the immutable WH-01 dataset. It must fail closed when a file/checksum is missing, replaced, malformed, unordered or does not cover every decision horizon.

## Acceptance criteria

- request rejects missing/unsafe authority fields, wrong symbols/date, holdout overlap and mismatched filenames;
- source archive hash must match its official checksum;
- traversal, encryption, multiple members, malformed rows and unsafe compression fail closed;
- headerless and recognized-header official representations parse deterministically;
- dataset manifest/partition/row tampering fails;
- every decision has a post-decision trade sequence reaching the exact 15-minute horizon;
- successful outputs reproduce the same manifest/checksum identities;
- output and source tampering fail independent verification;
- existing output roots are verified, never overwritten;
- compile, focused tests, Ruff/format and repository CI pass before merge;
- final diff stays within the four declared paths;
- no unresolved review thread or requested-change review remains.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-08-01T11:45:00+02:00
status: validating
branch: feat/wickhunter-wh02-replay-price-path-v1
base_branch: develop
context_routes:
  - AGENTS.md
  - docs/agents/programs/FTAI_WICKHUNTER_LIQUIDATION_BOT_PROGRAM.md
  - docs/agents/tasks/FTAI-20260731-wickhunter-wh01-production-materialization-v1.md
  - docs/ai_platform/WICKHUNTER_REPLAY_PRICE_PATH.md
  - ai_platform/wickhunter/replay_price_path.py
  - tests/ai_platform_integration/test_wickhunter_replay_price_path.py
owned_paths:
  - ai_platform/wickhunter/replay_price_path.py
  - tests/ai_platform_integration/test_wickhunter_replay_price_path.py
  - docs/ai_platform/WICKHUNTER_REPLAY_PRICE_PATH.md
  - docs/agents/tasks/FTAI-20260801-wickhunter-wh02-replay-price-path-v1.md
proven:
  - WH-01 production dataset is immutable, independently verified, contains 154 partitions and 919 rows, and remains before the protected holdout
  - all real decision timestamps occur inside open 5-minute candles
  - the current candle package cannot establish exact post-decision intrabar price order
  - compatibility-prior candidate activity is zero across all 1838 reversal/continuation evaluations
  - official Binance public data exposes public daily USD-M aggTrades archives and matching SHA-256 checksum files
  - the core importer can remain network-free and separate from a later request-only source acquisition operator
derived:
  - exact aggregate-trade sequence can remove the source-data blocker without choosing a replay entry/slippage convention
  - a successful source package must not itself authorize labels, replay or performance research
unknown:
  - exact availability, size, checksums and row counts of all required 2026-07-31 production archives until the separate trusted-runner request
  - maximum observed first-trade delay after each dataset decision
  - whether every required symbol archive provides uninterrupted temporal coverage through every horizon
  - final entry, fee, slippage, TP/SL ordering and label contracts
conflicts: []
first_failure: null
rejected_hypotheses:
  - treat a 5-minute candle high/low order as exact intrabar evidence
  - align decision timestamps backwards or forwards to candle boundaries
  - synthesize one-minute or trade-level paths from aggregate candles
  - change the compatibility prior inside a source-evidence package
  - claim replay readiness merely because WH-01 materialization succeeded
changed_paths:
  - ai_platform/wickhunter/replay_price_path.py
  - tests/ai_platform_integration/test_wickhunter_replay_price_path.py
  - docs/ai_platform/WICKHUNTER_REPLAY_PRICE_PATH.md
  - docs/agents/tasks/FTAI-20260801-wickhunter-wh02-replay-price-path-v1.md
validation:
  - command: Python syntax compile of implementation and focused tests before upload
    result: PASS
    evidence: both generated source texts compile with Python parser
blockers: []
next_action: open the four-file implementation PR, run focused validation and exact-head repository CI, repair only proven failures, then merge before creating a separate request-only archive acquisition/import operation
```
