---
task_id: FTAI-20260731-wickhunter-market-evidence-recovery-v1
status: in_progress
branch: agent/wickhunter-market-evidence-recovery-v1
base_branch: develop
created: 2026-07-31
updated: 2026-07-31
related_pr: 833
depends_on:
  - merged guarded WH-01 materialization operator from PR #723
  - merged production market-evidence implementation and repair from PRs #753 and #766
  - merged OKX Liquid20 source implementation from PR #761
  - active request-only production capture PR #816
owned_paths:
  - docs/agents/tasks/FTAI-20260731-wickhunter-market-evidence-recovery-v1.md
  - docs/agents/prompts/WICKHUNTER-MARKET-EVIDENCE-RECOVERY-AGENT-PROMPT.md
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/programs/FTAI_WICKHUNTER_LIQUIDATION_BOT_PROGRAM.md
  - docs/agents/tasks/FTAI-20260730-wickhunter-production-market-evidence-capture-and-portal-v1.md
  - docs/ai_platform/WICKHUNTER_PRODUCTION_MARKET_EVIDENCE.md
  - docs/ai_platform/portal/MARKET_EVIDENCE_READ_MODEL.md
---

# WickHunter market-evidence recovery v1

## Goal

Remove every truthful red Market Evidence state by completing source-separated OKX evidence, binding one compatible accepted Liquid20 archive to prospectively frozen WH-01 geometry, materializing a non-empty independently verified WH-01 dataset, and making Portal status derive only from those facts.

## Confirmed Gate 0 findings

1. `develop` was audited at `e19327315cd40d11bcaaa48b11dc53afa80d78e8`.
2. PR #816 is the active request-only lane at exact head `160ff749ada5e732fdbabfe885af1c29af668bbb`; its dedicated workflow run `30560769455` completed successfully.
3. The immutable request in PR #816 contains only `bybit-linear` and `binance-usdm`. Its identity must not be changed, reused or expanded to OKX.
4. The merged collector, publication service, WH-01 adapter and policy are frozen around two sources. Counts, source validation, candle artifacts and policy requirements are two-source contracts.
5. The Portal read model explicitly excludes `okx-swap` from candle, quality, instrument-history and WickHunter eligibility and returns `OKX_CANDLE_EVIDENCE_NOT_CONFIGURED`.
6. The merged Liquid20 source catalog and live collector already support public `okx-swap` liquidation events and immutable public instrument snapshots, but this is not equivalent to Market Evidence candle and quality coverage.
7. PR #758 does not own Market Evidence paths in its current diff. A current `develop...dc5c14a23d4dd5fff8b02390a4f79a7df61b5dee` comparison shows only four real-target preflight paths, so there is no current ownership collision.
8. The accepted Liquid20 import recorded by PR #716 is proven historical evidence, but compatibility with a future three-source Market Evidence package is not assumed and must pass a new binding verifier.
9. Full production completion is time-gated. A new three-source implementation must merge before a new prospective request can collect a real immutable interval.

## Required child packages

### A. Backward-compatible OKX Market Evidence

Create a focused mergeable package that preserves the exact v1 two-source request while adding a new versioned three-source contract for public OKX SWAP:

- public ticker, book, completed 5m candle and instrument endpoints only;
- exact native-to-canonical mapping;
- closed-candle availability semantics;
- deterministic source-separated quality, instrument and candle records;
- dynamic verified counts rather than two-source constants;
- credential, proxy, private/account/order and overwrite refusal;
- tamper, stale, gap, traversal, symlink and zero-order tests;
- Portal eligibility derived from verified package rows rather than a hard-coded OKX exclusion.

### B. Immutable archive binding and materialization

Create a separate mergeable package that validates and publishes a no-overwrite binding containing:

- accepted import/run and accepted-selection identities;
- archive and market-package digests;
- source, symbol and instrument mapping;
- decision cadence, history, purge, embargo and prospective split digest;
- temporal overlap, pre-roll and availability-time semantics;
- protected-holdout exclusion;
- a new materialization-request identity.

It must invoke the existing guarded WH-01 operator only after a fully ready preflight and independently verify a non-empty `wickhunter-dataset-manifest-v1`.

### C. Production operation

After A and B merge, create a new exact-one-file request-only PR with a new request/run identity. Deploy through the trusted Synology runner, leave sampling to the persistent collector, wait for the complete real interval, publish atomically, verify hashes/counts/gaps/source coverage and `orders_submitted == 0`, then close the request PR without merge.

### D. Terminal closure

Record exact implementation SHAs, workflow runs, operational artifact identities, binding digest, dataset manifest digest, Portal proof and one next action. Do not clear typed blockers before evidence exists.

## Safety invariants

```text
execution_enabled=false
trading_authorized=false
trading_credentials_present=false
orders_submitted=0
model_execution_authorized=false
replay_authorized=false
performance_research_authorized=false
live_capital_authorized=false
```

No credentials, private/account/order endpoints, proxy bypass, replay, training, optimization, execution, live capital, protected-holdout reuse, synthetic fallback, backdating, immutable mutation, force push or CI bypass.

## Acceptance criteria

The task remains incomplete until production evidence proves:

- no global `BLOCKED` or `WH-01 BLOCKED`;
- no `LIQUIDATION_ARCHIVE_NOT_BOUND` because a real accepted archive is cryptographically bound;
- verified OKX liquidation, candle, quality and instrument-history evidence;
- healthy Binance USD-M and Bybit Linear without regression;
- a non-empty immutable hash-verified WH-01 dataset with no unexplained accepted-window gaps;
- green exact-head CI, zero unresolved review threads and normal merges for mergeable packages;
- all safety invariants remain true.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-31T00:42:00+02:00
head: b18d1597b250faf09c99dda62704e8cc03121307
branch: agent/wickhunter-market-evidence-recovery-v1
status: in_progress
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
  - develop was audited at e19327315cd40d11bcaaa48b11dc53afa80d78e8.
  - PR 816 exact head 160ff749ada5e732fdbabfe885af1c29af668bbb has successful dedicated workflow run 30560769455.
  - PR 816 freezes only bybit-linear and binance-usdm and cannot truthfully be expanded to OKX.
  - Current collector, publication, WH-01 policy and Portal read model contain explicit two-source assumptions.
  - Current Portal OKX exclusion is a truthful code/configuration state, not a stale label.
  - Liquid20 already has public OKX liquidation and instrument contracts, but not the missing Market Evidence coverage.
  - PR 758 current effective diff is disjoint from Market Evidence paths.
derived:
  - A new versioned three-source implementation and a new prospective operational request are required.
  - The existing accepted Liquid20 import may be used only if the future binding verifier proves temporal and mapping compatibility.
unknown:
  - Exact future request window after implementation merge.
  - Which completed accepted Liquid20 archive will overlap the future evidence interval.
  - Terminal Synology artifact identities for the future three-source run.
conflicts: []
first_failure:
  marker: OKX_REQUIRED_SOURCE_ABSENT_FROM_FROZEN_REQUEST
  evidence: PR 816 request and merged v1 collector contract list only bybit-linear and binance-usdm, while Portal explicitly returns OKX_CANDLE_EVIDENCE_NOT_CONFIGURED.
rejected_hypotheses:
  - Mutate or reuse the PR 816 request identity to add OKX.
  - Treat public OKX liquidation events as candle and market-quality evidence.
  - Remove Portal blockers without a verified immutable package and dataset.
  - Retroactively freeze geometry or backdate instrument metadata.
  - Assume the PR 716 accepted import is compatible without binding verification.
changed_paths:
  - docs/agents/prompts/WICKHUNTER-MARKET-EVIDENCE-RECOVERY-AGENT-PROMPT.md
  - docs/agents/tasks/FTAI-20260731-wickhunter-market-evidence-recovery-v1.md
validation:
  - command: live repository, PR, workflow, source-contract and read-model audit
    result: PASS
    evidence: Gate 0 findings recorded above; prompt codespell defects fixed in commit b18d1597b250faf09c99dda62704e8cc03121307.
blockers:
  - Full green production state requires a future real three-source observation interval after merge of repository prerequisites.
next_action: Create the focused Package A child task and implementation branch from current develop, preserving the immutable v1 request while adding a versioned three-source OKX Market Evidence contract.
```
