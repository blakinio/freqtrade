---
task_id: FTAI-20260731-wickhunter-market-evidence-recovery-v1
status: ready
branch: agent/wickhunter-market-evidence-recovery-v1
base_branch: develop
created: 2026-07-31
updated: 2026-07-31
related_pr: null
depends_on:
  - merged guarded WH-01 materialization operator from PR #723
  - merged production market-evidence implementation and repair from PRs #753 and #766
  - terminal Liquid20 OKX source contract from PR #761, revalidated against live develop
  - active operational request PR #816, which must not be duplicated or merged
  - real production observations through the frozen interval ending 2026-07-31T18:00:00Z
owned_paths:
  - docs/agents/tasks/FTAI-20260731-wickhunter-market-evidence-recovery-v1.md
  - docs/agents/prompts/WICKHUNTER-MARKET-EVIDENCE-RECOVERY-AGENT-PROMPT.md
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/programs/FTAI_WICKHUNTER_LIQUIDATION_BOT_PROGRAM.md
  - docs/agents/programs/FTAI_AI_TRADING_PORTAL_PROGRAM.md
  - docs/agents/tasks/FTAI-20260730-wickhunter-production-market-evidence-capture-and-portal-v1.md
  - docs/ai_platform/WICKHUNTER_PRODUCTION_MARKET_EVIDENCE.md
  - docs/ai_platform/portal/MARKET_EVIDENCE_READ_MODEL.md
---

# WickHunter market-evidence recovery v1

## Goal

Remove every truthful red state on the WickHunter Market Evidence surface by completing the real source evidence, binding an eligible immutable Liquid20 archive to prospectively frozen WH-01 split geometry, materializing and independently verifying a non-empty WH-01 dataset, and making Portal status derive only from those verified facts.

This is an end-to-end recovery coordinator/operator task. It may create and execute several sequential focused child tasks and PRs, but it must not collapse implementation, production activation and immutable evidence publication into one unreviewable change.

## Initial observed symptoms

The supplied Portal evidence shows:

- global `BLOCKED` and `WH-01 BLOCKED`;
- blocker `LIQUIDATION_ARCHIVE_NOT_BOUND`;
- `OKX Swap` in `DEGRADED` state;
- OKX liquidation feed, candle evidence, market quality and instrument history reported unavailable;
- OKX WickHunter eligibility reported `excluded`;
- `OKX_CANDLE_EVIDENCE_NOT_CONFIGURED`;
- Binance USD-M and Bybit Linear reported healthy;
- an immutable run named `wickhunter-production-market-evidence-20260729-v1-r1`, 24 h pre-roll, four instruments and 3,456 completed candles.

These observations are only the starting report. The agent must refetch current repository, PR, workflow, Synology evidence and Portal state before drawing conclusions.

## Mandatory execution model

### Gate 0 — live truth and collision audit

Before editing implementation:

1. Fetch current `develop`, open PRs, active branches, task records, workflow conclusions, unresolved review threads and deployment checkpoints.
2. Inspect PR #816 and its exact workflow evidence. Do not open a duplicate request and never merge an operational request PR into `develop`.
3. Read the deployed Market Evidence read model and the immutable package pointed to by the Portal. Distinguish a truthful external-data blocker from a code, configuration, deployment or stale-read defect.
4. Revalidate all relevant identities, timestamps, source mappings, hashes and authority flags. Chat text and the screenshot are not authoritative.
5. Search ownership before editing. Create exact child task records with disjoint `owned_paths` for every required implementation package.

### Package A — complete OKX market evidence

If current live state confirms that OKX lacks candle or quality evidence, implement a separately reviewed, source-separated public OKX SWAP evidence path that:

- uses only public credential-free market and public instrument endpoints;
- rejects the presence of OKX credentials, private/account endpoints and order capability;
- captures only completed candles at the canonical cadence used by WH-01;
- records event/open/close/receive/availability timestamps and versioned source identity;
- publishes historical instrument snapshots and exact symbol/venue/market mappings;
- computes the same required market-quality and WH-01 metrics as the other eligible sources;
- preserves deterministic ordering, deduplication, restart recovery, gap accounting and atomic immutable publication;
- fails closed for missing, stale, conflicting or unverifiable data;
- never labels OKX healthy or eligible until independently verified evidence exists.

Do not retrofit old OKX liquidation events with fabricated candles or current-state instrument metadata.

### Package B — bind immutable evidence to WH-01 geometry

Implement or complete the exact binding boundary between:

- one accepted immutable Liquid20 archive/import identity and digest;
- one immutable market-evidence package identity and digest;
- exact source/instrument mapping;
- prospectively frozen decision cadence, history, purge, embargo and split geometry;
- protected-holdout exclusion;
- one no-overwrite materialization request identity.

The binding must validate temporal overlap, pre-roll, source coverage, symbol mapping, canonical hashes, accepted-selection identity and availability-time semantics. It must not mutate, rename, rewrite or silently substitute either immutable input.

If the required split geometry was not frozen before the relevant observations, reject retroactive geometry and prepare a new prospective run with new request/run identities. Never make the existing package pass by backdating policy state.

### Package C — production capture and immutable publication

Use the existing active capture when it remains valid. Repair only evidenced deployment/runtime defects and preserve its immutable request identity and durable state.

When a new run is genuinely required:

- create a new separately reviewed canonical request with a new identity;
- use the approved Synology runner and durable state root;
- release the self-hosted runner after bounded deployment/health confirmation;
- leave persistent sampling to the hardened collector;
- wait for the complete real interval and required pre-roll;
- publish atomically under a new immutable no-overwrite root;
- independently verify hashes, counts, gaps, freshness, instruments and `orders_submitted == 0`.

Operational request PRs are exact-scope triggers and must be closed without merge after terminal evidence is recorded.

### Package D — WH-01 materialization and independent verification

Run the existing guarded operator only after all bindings are ready. Require:

- preflight `ready` with no ignored blocker;
- a non-empty `wickhunter-dataset-manifest-v1`;
- deterministic rows, partitions, source identities and universe history;
- exact artifact hashes and independent re-verification;
- no future data, no protected holdout `20260801-20260930`, no synthetic fallback and no current-state backdating;
- all model, replay, performance-research, execution, trading and live-capital authority flags still false.

A materialization that merely changes Portal status without producing independently verified immutable data is a failure.

### Package E — Portal truth and operational closure

Update the Portal only when a live audit proves a read-model, cache, mapping or status derivation defect. The UI must:

- display source health independently;
- expose exact typed blockers while they exist;
- show OKX healthy/eligible only from verified OKX evidence;
- clear `LIQUIDATION_ARCHIVE_NOT_BOUND` only when the accepted archive digest is present in the verified binding and final manifest;
- clear global `BLOCKED` only when the complete WH-01 readiness contract passes;
- remain read-only and tenant-safe with no mutation or trading control.

After deployment, compare the Portal response with the immutable package and WH-01 verification output. Record exact terminal evidence and close stale operational PRs without merging them.

## Child-task and PR protocol

The recovery agent owns only this task and its launch prompt initially. Before changing implementation it must create one or more exact child task records and assign non-overlapping paths. Use focused branches and normal PRs against `develop`.

Separate at minimum:

1. mergeable repository implementation/repair;
2. exact-scope operational request or production execution;
3. terminal evidence/checkpoint closure.

Do not force-push, bypass CI, weaken fail-closed checks, merge a request-only PR, reuse a consumed request ID or overwrite immutable evidence.

## Acceptance criteria

The task is complete only when current production evidence proves all of the following:

- no global `BLOCKED` or `WH-01 BLOCKED` status remains;
- `LIQUIDATION_ARCHIVE_NOT_BOUND` is absent because an accepted immutable archive is cryptographically bound, not hidden;
- OKX has verified liquidation, candle, market-quality and instrument-history evidence and is `HEALTHY` and eligible, or a product decision explicitly removes OKX from the required WH-01 universe without falsifying health;
- Binance USD-M and Bybit Linear remain healthy without regression;
- the immutable package and final WH-01 dataset are non-empty, hash-verified, source-separated and temporally valid;
- completed candles have zero unexplained gaps for the accepted interval;
- `execution_enabled=false`, `trading_authorized=false`, `trading_credentials_present=false`, `orders_submitted=0`, `model_execution_authorized=false`, `replay_authorized=false`, `performance_research_authorized=false` and `live_capital_authorized=false`;
- exact-head required CI is green, unresolved review threads are zero and mergeable implementation PRs are merged normally;
- the task checkpoint contains exact commits, workflow runs, artifact identities, hashes, counts, first failure, rejected hypotheses and exactly one next action.

If a real future observation window or unavailable external runner is the only remaining blocker, do not claim completion. Finish every repository-side prerequisite, record the exact blocker and resumable next action, and leave all red states truthful.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-31T00:04:00+02:00
head: null
branch: agent/wickhunter-market-evidence-recovery-v1
status: ready
context_routes:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/tasks/FTAI-20260731-wickhunter-market-evidence-recovery-v1.md
  - docs/agents/tasks/FTAI-20260730-wickhunter-production-market-evidence-capture-and-portal-v1.md
  - docs/ai_platform/WICKHUNTER_PRODUCTION_MARKET_EVIDENCE.md
  - docs/ai_platform/portal/MARKET_EVIDENCE_READ_MODEL.md
owned_paths:
  - docs/agents/tasks/FTAI-20260731-wickhunter-market-evidence-recovery-v1.md
  - docs/agents/prompts/WICKHUNTER-MARKET-EVIDENCE-RECOVERY-AGENT-PROMPT.md
proven:
  - The merged repository already contains a guarded WH-01 materialization operator and production Market Evidence collector/read model.
  - The prior task explicitly kept OKX liquidation-only and WH-01 blocked until an accepted liquidation archive and frozen split geometry are bound.
  - PR 816 is an operational request lane and must be inspected rather than duplicated or merged.
  - The observed Portal state reports LIQUIDATION_ARCHIVE_NOT_BOUND and OKX_CANDLE_EVIDENCE_NOT_CONFIGURED.
derived:
  - A complete repair requires evidence collection, immutable binding, materialization and Portal verification; changing UI labels alone cannot satisfy the task.
unknown:
  - Current terminal state and durable artifact identity of PR 816.
  - Whether the current immutable run covers the required final interval and has prospectively frozen valid geometry.
  - Which accepted Liquid20 archive is contemporaneous and mapping-compatible with the final market-evidence package.
  - Whether OKX candle support requires new source implementation, deployment configuration, or only activation of already merged code.
conflicts: []
first_failure:
  marker: INITIAL_PORTAL_RED_STATE
  evidence: User-supplied Market Evidence view reports global WH-01 blocking and incomplete OKX evidence.
rejected_hypotheses:
  - Clear red UI state without producing or verifying missing evidence.
  - Treat OKX liquidation-only data as complete candle and market-quality evidence.
  - Bind an archive with guessed identity, mismatched interval or incomplete symbol mapping.
  - Retroactively invent split geometry after observing the data.
  - Mutate or overwrite accepted immutable evidence.
  - Enable replay, models, execution, credentials, orders or live-capital authority.
changed_paths:
  - docs/agents/tasks/FTAI-20260731-wickhunter-market-evidence-recovery-v1.md
validation:
  - command: repository live-state audit
    result: PENDING
    evidence: Recovery agent has not been launched yet.
blockers: []
next_action: Launch the recovery agent from docs/agents/prompts/WICKHUNTER-MARKET-EVIDENCE-RECOVERY-AGENT-PROMPT.md and execute Gate 0 against current live repository and production evidence before creating child implementation tasks.
```
