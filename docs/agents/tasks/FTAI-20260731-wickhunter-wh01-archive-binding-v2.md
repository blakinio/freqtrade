---
task_id: FTAI-20260731-wickhunter-wh01-archive-binding-v2
status: in_progress
branch: agent/wickhunter-wh01-archive-binding-v2
base_branch: develop
created: 2026-07-31
updated: 2026-07-31
related_pr: null
depends_on:
  - FTAI-20260731-wickhunter-okx-market-evidence-v2
  - accepted immutable Liquid20 import
  - accepted immutable three-source Market Evidence v2 package
owned_paths:
  - ai_platform/wickhunter/liquid20_archive_binding_v2.py
  - ai_platform/wickhunter/production_market_evidence_wh01_v2.py
  - tests/ai_platform_integration/test_wickhunter_liquid20_archive_binding_v2.py
  - tests/ai_platform_integration/test_wickhunter_production_market_evidence_wh01_v2.py
  - docs/agents/tasks/FTAI-20260731-wickhunter-wh01-archive-binding-v2.md
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/tasks/FTAI-20260731-wickhunter-market-evidence-recovery-v1.md
  - docs/agents/tasks/FTAI-20260731-wickhunter-okx-market-evidence-v2.md
  - ai_platform/wickhunter/materialization.py
  - ai_platform/wickhunter/production_market_evidence_wh01.py
---

# WickHunter WH-01 archive binding v2

## Goal

Create the fail-closed cryptographic boundary that binds one accepted immutable Liquid20 import to one accepted immutable three-source Market Evidence v2 package and one prospectively frozen WH-01 geometry, then invoke the existing guarded materializer only after every compatibility check passes.

## Required behavior

- verify accepted import/run identity, archive digest and accepted-selection digest;
- verify complete three-source Market Evidence v2 package, package digest, source-package binding and authority boundary;
- verify exact symbols, source mappings, interval overlap, minimum pre-roll and availability-time semantics;
- verify policy, decision cadence, history, purge, embargo, split and protected-holdout boundaries;
- publish a new immutable no-overwrite binding with a self hash;
- create a new materialization request identity only after binding acceptance;
- invoke existing guarded materialization without ignored blockers;
- independently verify a non-empty `wickhunter-dataset-manifest-v1` and all referenced hashes;
- remain blocked when the required production artifacts do not yet exist.

## Safety

No mutation of immutable inputs, no backdating, no synthetic fallback, no guessed mapping, no holdout reuse, no replay, model execution, performance research, orders, execution or live capital.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-31T02:05:00+02:00
head: 5d608dd617d6a5e14ee197fc4b34b887d55bbbe2
branch: agent/wickhunter-wh01-archive-binding-v2
pr: null
status: in_progress
context_routes:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/tasks/FTAI-20260731-wickhunter-wh01-archive-binding-v2.md
owned_paths:
  - ai_platform/wickhunter/liquid20_archive_binding_v2.py
  - ai_platform/wickhunter/production_market_evidence_wh01_v2.py
  - tests/ai_platform_integration/test_wickhunter_liquid20_archive_binding_v2.py
  - tests/ai_platform_integration/test_wickhunter_production_market_evidence_wh01_v2.py
  - docs/agents/tasks/FTAI-20260731-wickhunter-wh01-archive-binding-v2.md
proven:
  - Existing materialization is guarded and already validates accepted imports, market context, universe history and build request identities.
  - The Market Evidence v2 package deliberately retains LIQUIDATION_ARCHIVE_NOT_BOUND until this boundary succeeds.
  - Production artifacts are not yet terminal and therefore cannot be truthfully bound now.
derived:
  - Repository implementation can be completed before the real capture interval ends, while publication remains blocked on terminal immutable inputs.
unknown:
  - Terminal accepted v1 and OKX package hashes.
  - Terminal accepted Liquid20 import selected for the overlapping interval.
conflicts: []
first_failure:
  marker: LIQUIDATION_ARCHIVE_NOT_BOUND
  evidence: No immutable binding currently references both an accepted Liquid20 archive and the final Market Evidence package.
rejected_hypotheses:
  - Clear the blocker in Portal without a binding artifact.
  - Reuse an incompatible historical archive without temporal and mapping verification.
  - Freeze split geometry after inspecting terminal evidence.
changed_paths:
  - docs/agents/tasks/FTAI-20260731-wickhunter-wh01-archive-binding-v2.md
validation:
  - command: ownership and existing materializer contract audit
    result: PASS
    evidence: New owned paths do not overlap the implementation or operational request package.
blockers:
  - Terminal production artifacts are required before binding publication and materialization.
next_action: Implement the immutable binding verifier and v2 adapter against the existing guarded materialization contract, with terminal publication kept fail-closed.
```
