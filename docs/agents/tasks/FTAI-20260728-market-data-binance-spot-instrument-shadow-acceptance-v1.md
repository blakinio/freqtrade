---
task_id: FTAI-20260728-market-data-binance-spot-instrument-shadow-acceptance-v1
status: validating
branch: trigger/binance-v3-shadow-acceptance-20260729
base_branch: develop
created: 2026-07-28
updated: 2026-07-31
related_pr: "#738"
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/ai_platform/market_data/BINANCE_SPOT_INSTRUMENT_SHADOW_ACCEPTANCE_V3.md
search_first:
  - workflow 30482434626 and initializer job 90679668485
  - observer workflow 30645984529 and job 91207351730
  - cadence diagnostic workflow 30647694832 and job 91213062987
---

# Binance Spot instrument shadow acceptance v1

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-31T18:38:00+02:00
head: 72cdd4613bba59a02aa3ab7cac3c29774929b5d5
branch: trigger/binance-v3-shadow-acceptance-20260729
pr: "#738"
status: validating
proven:
  - Exact-one-file trigger PR 738 initialized immutable run binance-spot-instrument-shadow-acceptance-20260729-v3-r1 and was closed without merge.
  - Read-only observer workflow 30645984529 job 91207351730 recorded 21 of 97 samples in artifact 8799420811.
  - Read-only cadence diagnostic PR 873 was closed without merge after workflow 30647694832 job 91213062987 succeeded.
  - Diagnostic artifact 8800097750 has digest sha256:f5deaf541352cf28d2d8e3377e1f33a4d4606b15762af380e02ec1446d9e9e16.
  - At 2026-07-31T18:35:20+02:00 the durable run was active with 22 of 97 samples; the latest sample completed at 2026-07-31T18:20:47.154027+02:00.
  - Only 26 scheduled runs were emitted after the window start versus approximately 545 expected at a five-minute cadence.
  - Scheduled-run creation gaps had minimum 3120 seconds, median 5918 seconds and maximum 12510 seconds.
  - Run 30496430843 was created at 2026-07-29T22:31:21Z, but job 90726251065 reached freqtrade-synology-staging at 2026-07-30T06:23:43Z, approximately 7 hours 52 minutes later.
  - Cancelled runs 30499926270, 30504219662 and 30512386643 contain no jobs, proving cancellation before runner pickup.
  - Terminal summary, manifest, report and checksum files remain absent; source_acceptance=false, production_source_enabled=false and orders_submitted=0.
derived:
  - The primary cadence failure is sparse GitHub schedule emission.
  - A secondary failure is prolonged contention on the single shared runner, followed by replacement of older pending runs in the workflow concurrency group.
  - The present GitHub-cron plus shared-runner architecture cannot reliably satisfy the intended 15-minute observation cadence.
unknown:
  - Exact competing workload or workloads that occupied the runner during the approximately 7-hour-52-minute delay.
  - Terminal accepted, rejected or inconclusive outcome and completion time.
conflicts: []
first_failure:
  marker: BINANCE_ACCEPTANCE_SCHEDULER_CADENCE_UNRELIABLE
  evidence: Only 26 scheduled runs were emitted versus approximately 545 expected, one sampler waited nearly eight hours for the shared runner and three pending runs were cancelled before job creation.
rejected_hypotheses:
  - Treat the stale checkpoint as proof that the durable run stopped.
  - Treat Binance request duration or the incremental due check as the main bottleneck.
  - Rerun, retry, reopen or reuse consumed trigger identities.
changed_paths:
  - docs/agents/tasks/FTAI-20260728-market-data-binance-spot-instrument-shadow-acceptance-v1.md
validation:
  - command: Read-only cadence diagnostic workflow 30647694832 job 91213062987
    result: PASS
    evidence: Artifact 8800097750 correlated durable progress with sparse scheduled emissions, runner contention and pre-job cancellations.
  - command: GitHub PR 873 terminal state
    result: PASS
    evidence: Exact-one-file diagnostic PR closed without merge.
blockers:
  - Seventy-five observations remain and the existing scheduler cannot guarantee the required cadence.
next_action: Prepare a separately reviewed design-only cadence repair proposal that replaces best-effort GitHub cron and shared-runner dependence without modifying or restarting the active immutable run.
```
