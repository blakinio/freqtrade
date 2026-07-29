---
task_id: FTAI-20260728-wickhunter-production-live-archive-conversion-v1
status: completed
branch: docs/wickhunter-production-conversion-terminal-pass-20260729
base_branch: develop
created: 2026-07-28
updated: 2026-07-29
related_pr: 712
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
checkpoint_version: 2
updated_at: 2026-07-29T17:47:00+02:00
status: completed
implementation:
  operator_pr: 659
  validated_code_head: 052dbd17b31d3b5b0dff54931675b792847d45c2
  merged_commit: 309770a579920645f58d989f02ea27220ff64d25
  runtime_import_fix_pr: 680
  runtime_import_fix_merge: 3acabedc60307d1fb232cc02d14f9e34d7652757
  restart_state_fix_pr: 683
  restart_state_fix_merge: f898c01dd3f3165571be257eee3947b555124bad
  restart_count_fix_pr: 694
  restart_count_validated_head: 88d3d238be9e9757dd585bea8ac7dfcd3e5cedcb
  restart_count_fix_merge: 99d965436f623f56c3c2c08d9207b926bd42aae4
terminal_operation:
  trigger_pr: 712
  trigger_pr_merged: false
  trigger_head: 5f017ad3d5a5ba391f1c4fcf7dd379bb88ef44b6
  workflow_run: 30467059746
  workflow_job: 90627434486
  workflow_result: success
  operation_id: wickhunter-production-live-archive-20260729-v4
  selected_run_id: liquid20-20260729T000000Z-0
  selected_run_completed_at_ms: 1785328106245
  selection_sha256: 1056ff8a100f67f7e5eed69d5a97d9351bd4689205cbdc033fe196cdaee53f3b
  import_run_id: first-party-live:liquid20-20260729T000000Z-0:7a1a5fc5c22c4d5d
  input_identity_sha256: 7a1a5fc5c22c4d5df37cb3df09889c156e597a2f0bb08be8fad302efac8a88ea
  immutable_wh01_verification: success
accepted_evidence:
  status: pass
  accepted_records: 29253
  total_records: 29253
  rejected_records: 0
  duplicate_records: 0
  concrete_symbols: 621
  manifest_multi_symbol_descriptor: true
  earliest_occurred_at_ms: 1785283200052
  latest_occurred_at_ms: 1785328080434
  observed_duration_hours: 12.4668
  minimum_availability_latency_ms: 93
  maximum_availability_latency_ms: 12278
  protected_holdout_start_ms: 1785542400000
  protected_holdout_excluded: true
  provider_id: first-party
  license_classification: first-party-public-market-data
  sources:
    binance-usdm:
      declared_events_written: 21402
      actual_events_written: 21402
      reconciled_event_count_delta: 0
      restart_state_accepted: true
      restart_count_reconciled: false
      events_sha256: 08a0b5587863cf08a5f1532cf9ca7a5049e063ef0253b0a5c664394052021590
    bybit-linear:
      declared_events_written: 7850
      actual_events_written: 7851
      reconciled_event_count_delta: 1
      restart_state_accepted: true
      restart_count_reconciled: true
      events_sha256: 465a110c761fc876bf690dd5210531239fbd9c101d8eeb80b8fecacf381c7547
artifact_evidence:
  artifact_id: 8730084102
  artifact_name: wickhunter-production-live-archive-712
  artifact_size_bytes: 9325
  artifact_digest: sha256:39e6180a527e39f89de1ad11e76cfa0c15d0e9c68d400bc7699b95ca297e2d47
  artifact_expires_at: 2026-08-28T15:43:52Z
  manifest_sha256: 41ba4bf66ca371462f63a223ce37de1ca3be9cec236e8946105fbd753eecd32b
  events_sha256: 9303161c3559eec7d68fc8e3bb9a46605e8861d73557758808870f6242eeee04
  acceptance_sha256: 92433db3c1a5767eca9ee0c0596c7091a6d8eb24bec2a033cd5014945b232553
  source_run_sha256: 9df41d05d7dc87876ea4faaf80b128bb99abdd188a639b55b5d7356383d5a516
  accepted_artifact_index_sha256: 799730dd34b62d7161f480160d6bfce0824b92924eec593c5774bf6d79d9f870
  accepted_event_ids_sha256: 7141e77a27d2c352774cd0180656d3391a1197806433656357dafec811783e7f
authority_boundary:
  trading_credentials_present: false
  trading_authorized: false
  execution_enabled: false
  model_execution_authorized: false
  live_capital_authorized: false
  profitability_claimed: false
  strategy_quality_claimed: false
  wh02_authorized_by_conversion_alone: false
failed_attempts:
  - pr: 663
    workflow_run: 30393986107
    reason: isolated helper image imported an unavailable optional jsonschema dependency
    resolution: PR 680 merged; trigger closed without merge
  - pr: 681
    workflow_run: 30454202567
    reason: collector-restart closed only the root run state while source summaries remained active
    resolution: PR 683 merged; trigger closed without merge
  - pr: 691
    workflow_run: 30457898396
    reason: immutable Bybit NDJSON contained one valid event after the last persisted events_written checkpoint
    resolution: PR 694 merged; trigger closed without merge
proven:
  - The separately reviewed operator executes only from an exact-one-file same-repository pull request on the approved freqtrade-synology-staging runner.
  - Production Liquid20 input remained read-only, helper networking was disabled, the root filesystem was read-only and all capabilities were dropped.
  - The latest completed non-empty run before the protected holdout was selected deterministically.
  - The immutable accepted package passed the unchanged historical acceptance contract and a separate unchanged WH-01 load_accepted_import verification.
  - All 29253 events were accepted with zero rejections and zero duplicates.
  - The exact collector-restart compatibility reconciled only one additional valid Bybit record after the persisted checkpoint; all source and artifact identities remained hashed and immutable.
  - PR 712 was closed without merge after terminal evidence review.
derived:
  - The real accepted immutable dataset dependency named by the WH-02 program entry now exists.
  - This single approximately 12.47-hour run is broad in symbol count but is not by itself proof of regime diversity, replay stability, strategy quality or profitability.
  - Conversion completion does not itself create model, replay, trading, execution or live-capital authority; WH-02 requires a fresh bounded task and ownership preflight.
unknown:
  - Whether one short production interval is sufficient for every WH-02 evaluation slice and walk-forward geometry.
  - Which additional accepted immutable intervals should be selected later for regime and temporal diversity.
conflicts: []
blockers: []
validation:
  - command: AI Platform CI 30465682330
    result: PASS
    evidence: Exact restart-count repair head 88d3d238be9e9757dd585bea8ac7dfcd3e5cedcb passed platform tests, Ruff, format and codespell.
  - command: Freqtrade CI 30465673835
    result: PASS
    evidence: Exact repair head passed pre-commit, documentation, Python 3.11 through 3.14, full 3.12 coverage, distribution build and CI Gate.
  - command: GitHub Actions security analysis 30465687873
    result: PASS
    evidence: Exact repair head completed successfully.
  - command: WickHunter production conversion 30467059746
    result: PASS
    evidence: Job 90627434486 converted the selected production run, independently loaded the package through unchanged WH-01, uploaded bounded metadata and removed staged source data.
next_action: Open a fresh WH-02 ownership and dataset-adequacy preflight that binds this accepted import identity without claiming regime diversity or replay authority from conversion alone.
```
