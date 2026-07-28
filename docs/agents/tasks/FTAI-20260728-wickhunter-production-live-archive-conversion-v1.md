---
task_id: FTAI-20260728-wickhunter-production-live-archive-conversion-v1
status: validating
branch: run/wickhunter-production-live-archive-conversion-20260728-v1
base_branch: develop
created: 2026-07-28
updated: 2026-07-28
related_pr: 663
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
updated_at: 2026-07-28T21:56:00+02:00
validated_code_head: 052dbd17b31d3b5b0dff54931675b792847d45c2
merged_commit: 309770a579920645f58d989f02ea27220ff64d25
branch: run/wickhunter-production-live-archive-conversion-20260728-v1
pr: 663
status: validating
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
  - Operator implementation PR 659 merged as 309770a579920645f58d989f02ea27220ff64d25 after exact-head validation.
  - AI Platform CI run 30392705867 passed, including 912 tests, Ruff, format, codespell and JSON validation.
  - Freqtrade CI run 30392705874 passed, including pre-commit, documentation, Python 3.11 through 3.14, full 3.12 coverage, distribution build and CI Gate.
  - GitHub Actions security analysis run 30392705866 passed.
  - The implementation changed exactly the five declared owned paths and had no review threads or submitted reviews.
  - Exact-one-file request PR 663 at d3a8ca8e879adaea7408225d9fdbed5370f0094c opened against implementation merge 309770a579920645f58d989f02ea27220ff64d25.
  - WickHunter conversion workflow run 30393986107 and job 90392294701 exist and are queued without having executed a step.
  - The dedicated runner is occupied by governed OKX 24-hour acceptance run 30358400049, job 90271896559, whose frozen acceptance step remains in progress.
  - No WickHunter production run has yet been selected, read or converted.
derived:
  - The WickHunter request is correctly serialized behind the existing dedicated-runner workload rather than bypassing or cancelling it.
  - No alternate runner, Docker host, proxy, VPN or direct host-shell conversion is authorized.
  - Conversion success alone remains insufficient to claim strategy quality, profitability, regime diversity or WH-02 readiness.
unknown:
  - Which production closed run the deterministic selection will choose.
  - The accepted event count, duration, symbol coverage and regime diversity of that run.
  - The terminal result of conversion workflow run 30393986107.
conflicts: []
first_failure: null
rejected_hypotheses:
  - Cancel or weaken the active governed OKX acceptance to free the runner.
  - Run conversion directly from an unrestricted shell on the host.
  - Use an alternate runner or host path not reviewed by PR 659.
  - Mount the production Liquid20 data root writable.
  - Upload the complete accepted events file to GitHub Actions.
  - Start WH-02 or claim model/strategy evidence before terminal conversion review.
changed_paths:
  - .github/workflows/wickhunter-production-live-archive-conversion.yml
  - ai_platform/scripts/wickhunter_live_archive_conversion.py
  - tests/ai_platform_integration/test_wickhunter_live_archive_conversion.py
  - docs/ai_platform/WICKHUNTER_PRODUCTION_LIVE_ARCHIVE_CONVERSION.md
  - docs/agents/tasks/FTAI-20260728-wickhunter-production-live-archive-conversion-v1.md
validation:
  - command: AI Platform CI 30392705867
    result: PASS
    evidence: Exact implementation head 052dbd17b31d3b5b0dff54931675b792847d45c2 completed successfully.
  - command: Freqtrade CI 30392705874
    result: PASS
    evidence: Exact implementation head passed all required jobs and final CI Gate.
  - command: GitHub Actions security analysis 30392705866
    result: PASS
    evidence: Exact implementation head completed successfully.
  - command: production conversion workflow 30393986107
    result: NOT_RUN
    evidence: Job 90392294701 remains queued behind active governed OKX job 90271896559.
blockers:
  - The sole approved runner freqtrade-synology-staging is occupied by governed OKX 24-hour acceptance run 30358400049; do not cancel or bypass it.
next_action: Observe existing WickHunter workflow run 30393986107 after the approved runner becomes available, capture terminal metadata and immutable WH-01 verification, close PR 663 without merge, then update this checkpoint without starting WH-02 prematurely.
```
