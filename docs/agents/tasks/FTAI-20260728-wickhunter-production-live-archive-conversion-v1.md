---
task_id: FTAI-20260728-wickhunter-production-live-archive-conversion-v1
status: implementing
branch: ops/wickhunter-production-live-archive-conversion-v1
base_branch: develop
created: 2026-07-28
updated: 2026-07-28
related_pr: null
depends_on:
  - FTAI-20260728-wickhunter-live-archive-acceptance-bridge
owned_paths:
  - .github/workflows/wickhunter-production-live-archive-conversion.yml
  - ai_platform/scripts/wickhunter_live_archive_conversion.py
  - tests/ai_platform_integration/test_wickhunter_live_archive_conversion.py
  - docs/ai_platform/WICKHUNTER_PRODUCTION_LIVE_ARCHIVE_CONVERSION.md
  - docs/agents/tasks/FTAI-20260728-wickhunter-production-live-archive-conversion-v1.md
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/programs/FTAI_WICKHUNTER_LIQUIDATION_BOT_PROGRAM.md
  - docs/agents/tasks/FTAI-20260728-wickhunter-live-archive-acceptance-bridge.md
  - docs/ai_platform/WICKHUNTER_LIVE_ARCHIVE_ACCEPTANCE.md
  - deploy/synology/liquid20/LIVE_STREAM.md
---

# WickHunter production live archive conversion v1

## Goal

Add a separately reviewed exact-one-request Synology operator that selects one completed non-empty production Liquid20 live run, converts it read-only through the merged WickHunter bridge into an atomic immutable state root, and independently verifies the result with unchanged WH-01 `load_accepted_import()`.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-28T21:20:00+02:00
validated_code_head: null
merged_commit: null
branch: ops/wickhunter-production-live-archive-conversion-v1
pr: null
status: implementing
context_routes:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/programs/FTAI_WICKHUNTER_LIQUIDATION_BOT_PROGRAM.md
  - docs/agents/tasks/FTAI-20260728-wickhunter-live-archive-acceptance-bridge.md
  - docs/ai_platform/WICKHUNTER_LIVE_ARCHIVE_ACCEPTANCE.md
  - deploy/synology/liquid20/LIVE_STREAM.md
owned_paths:
  - .github/workflows/wickhunter-production-live-archive-conversion.yml
  - ai_platform/scripts/wickhunter_live_archive_conversion.py
  - tests/ai_platform_integration/test_wickhunter_live_archive_conversion.py
  - docs/ai_platform/WICKHUNTER_PRODUCTION_LIVE_ARCHIVE_CONVERSION.md
  - docs/agents/tasks/FTAI-20260728-wickhunter-production-live-archive-conversion-v1.md
proven:
  - The merged bridge accepts only completed immutable historical live runs and publishes a WH-01-compatible package atomically without overwrite.
  - The dedicated Synology runner has a durable state mapping at /var/lib/freqtrade-staging-state to host /volume1/docker/freqtrade/state.
  - The production Liquid20 data root is /volume1/docker/freqtrade-liquidations/data and must remain read-only to this operation.
  - The workflow trigger is restricted to one internal PR adding exactly one canonical request file.
  - The helper uses the exact running runner image ID, no network, read-only root, dropped capabilities, no-new-privileges and bounded memory.
  - The durable events.jsonl is not uploaded to GitHub; only bounded metadata and provenance are uploaded.
derived:
  - A successful one-shot run can satisfy the real accepted-import gate without mutating the collector or purchasing Tardis history.
  - Conversion success alone is insufficient to claim strategy quality, profitability, regime diversity or WH-02 readiness.
unknown:
  - Which production closed run the deterministic selection will choose.
  - The accepted event count, duration, symbol coverage and regime diversity of that run.
conflicts: []
first_failure: null
rejected_hypotheses:
  - Run conversion directly from an unrestricted shell on the host.
  - Mount the production Liquid20 data root writable.
  - Upload the complete accepted events file to GitHub Actions.
  - Let a malformed newest candidate silently fall back to older evidence.
  - Start WH-02 or claim model/strategy evidence before terminal conversion review.
changed_paths:
  - .github/workflows/wickhunter-production-live-archive-conversion.yml
  - ai_platform/scripts/wickhunter_live_archive_conversion.py
  - tests/ai_platform_integration/test_wickhunter_live_archive_conversion.py
  - docs/ai_platform/WICKHUNTER_PRODUCTION_LIVE_ARCHIVE_CONVERSION.md
  - docs/agents/tasks/FTAI-20260728-wickhunter-production-live-archive-conversion-v1.md
validation:
  - command: focused conversion operator tests
    result: NOT_RUN
    evidence: Awaiting exact-head CI.
  - command: repository pre-commit and Python matrix
    result: NOT_RUN
    evidence: Awaiting exact-head CI.
  - command: GitHub Actions security analysis
    result: NOT_RUN
    evidence: Awaiting exact-head CI.
blockers: []
next_action: Open the implementation PR, fix any exact-head CI or review findings, merge the operator, then create one exact-one-file request PR to perform the first production conversion and close that trigger without merge after terminal evidence.
```
