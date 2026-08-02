---
task_id: FTAI-20260802-wickhunter-deterministic-replay-window-index-v1
repository: blakinio/freqtrade
status: implementing
phase: implementation
owner: autonomous-agent
created_at: 2026-08-02
updated_at: 2026-08-02
related_pr: null
blocked_by: []
next_action: implement one-time symbol path validation and exact replay-window slicing; validate semantic parity and exact-head CI
---

# WickHunter deterministic replay window index v1

## Objective

Remove repeated whole-symbol trade-path validation from every decision and side while preserving the exact WH-02 label contract.

## Scope

- validate ordering, uniqueness and symbol identity once per normalized symbol partition;
- build one timestamp index per symbol;
- slice from the first entry-eligible trade through every trade on the exact label deadline, or include the first later trade only as the coverage witness;
- keep `replay_event_label` semantics and public API unchanged;
- add focused regression proving irrelevant pre/post-window trades are not passed into each label evaluation and same-deadline trades remain included.

## Safety invariants

- no protected holdout access;
- no source or policy mutation;
- no credentials, model work, execution, orders or live capital;
- deterministic label identities and serialized package format unchanged.
