---
task_id: FTAI-20260727-liquidation-okx-shadow-acceptance-v1
status: ready
branch: docs/okx-shadow-acceptance-policy-v1
base_branch: develop
created: 2026-07-27
updated: 2026-07-27
related_pr: "#413"
owned_paths:
  - ai_platform/research/liquidations/okx-liquidation-shadow-acceptance-policy-v1.json
  - docs/ai_platform/LIQUIDATION_OKX_SHADOW_ACCEPTANCE.md
  - docs/agents/tasks/FTAI-20260727-liquidation-okx-shadow-acceptance-v1.md
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/ai_platform/ARCHITECTURE.md
  - docs/ai_platform/ROADMAP.md
  - docs/ai_platform/LIQUIDATION_OKX_SHADOW_SOURCE.md
  - docs/ai_platform/LIQUIDATION_OKX_SHADOW_SMOKE.md
  - docs/ai_platform/LIQUIDATION_OKX_SHADOW_ACCEPTANCE.md
search_first:
  - current develop and open OKX liquidation ownership
  - merged short-smoke evidence and existing 24-hour liquidation acceptance policy
optional_reads: []
---

# OKX liquidation shadow acceptance v1

## Goal

Prospectively freeze the exact 24-hour operational acceptance contract for the isolated public OKX liquidation shadow source before any runner, evaluator, workflow or operational trigger exists.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-27T00:30:00+02:00
head: ad735c3e9639173553d20a0c02d1784c959f47a1
branch: docs/okx-shadow-acceptance-policy-v1
pr: "#413"
status: ready
context_routes:
  - docs/ai_platform/LIQUIDATION_OKX_SHADOW_SOURCE.md
  - docs/ai_platform/LIQUIDATION_OKX_SHADOW_SMOKE.md
  - docs/ai_platform/LIQUIDATION_OKX_SHADOW_ACCEPTANCE.md
owned_paths:
  - ai_platform/research/liquidations/okx-liquidation-shadow-acceptance-policy-v1.json
  - docs/ai_platform/LIQUIDATION_OKX_SHADOW_ACCEPTANCE.md
  - docs/agents/tasks/FTAI-20260727-liquidation-okx-shadow-acceptance-v1.md
proven:
  - Current develop f81a1f5a492c238032d3b30f481f7a52ae9ca546 records the merged and independently verified two-minute OKX public transport smoke.
  - PR 394 merged durable smoke identity while keeping raw NDJSON outside Git and OKX outside liquid20-v1.
  - No open PR owns an OKX long-run acceptance policy, runner, workflow or evidence path.
  - Existing liquid20-multi-source-acceptance-v1 prospectively freezes a 24-hour duration, 0.995 availability, at most 2.0 disconnects per hour, zero parser failures, 0.01 duplicate ratio and a 5000 ms latency threshold.
  - This declaration freezes the same health geometry for unchanged BTCUSDT and ETHUSDT OKX shadow collection and adds an explicit inconclusive outcome for insufficient real-event activity.
  - The declaration requires public endpoints, no credentials, zero orders, exact instrument metadata, start/end clock probes, self-hashed evidence and durable raw storage beyond an expiring CI artifact.
  - PR 413 contains exactly the three declared policy, runbook and checkpoint files and no implementation or operational trigger.
  - Exact content head ad735c3e9639173553d20a0c02d1784c959f47a1 passed AI Platform CI 30223119700, Freqtrade CI 30223119703 including CI Gate, and zizmor 30223119716.
  - GitHub reports PR 413 mergeable and there are no review threads.
derived:
  - The first long run should preserve the two-symbol smoke contract; broad-universe or liquid20-v2 membership is a later package.
  - A GitHub-hosted runner is not eligible for continuous 24-hour capture and durable raw evidence.
  - Zero or sparse events must not produce acceptance; healthy low-activity runs should be inconclusive rather than falsely rejected for transport quality.
unknown:
  - Exact implementation design for the inert runner, evaluator and guarded staging workflow.
  - Whether the intended non-restricted always-on Linux staging host will pass the frozen gates.
  - Final repository CI outcome for this ready-state checkpoint metadata commit.
conflicts: []
first_failure:
  marker: none
  evidence: The declaration content passed all required exact-head checks without a confirmed failure.
rejected_hypotheses:
  - Add OKX directly to liquid20-v1 after the short smoke.
  - Run a 24-hour job on a GitHub-hosted runner.
  - Permit zero events to satisfy long-run acceptance.
  - Treat quiet-market activity as a transport failure when all non-activity gates pass.
  - Implement or trigger collection before the policy is merged prospectively.
changed_paths:
  - ai_platform/research/liquidations/okx-liquidation-shadow-acceptance-policy-v1.json
  - docs/ai_platform/LIQUIDATION_OKX_SHADOW_ACCEPTANCE.md
  - docs/agents/tasks/FTAI-20260727-liquidation-okx-shadow-acceptance-v1.md
validation:
  - command: AI Platform CI 30223119700
    result: PASS
    evidence: Exact content head ad735c3e9639173553d20a0c02d1784c959f47a1 passed AI tests, Ruff, Ruff format, codespell and JSON validation.
  - command: Freqtrade CI 30223119703
    result: PASS
    evidence: Exact content head passed pre-commit, documentation build and CI Gate; core matrices were correctly skipped for the declaration-only scope.
  - command: GitHub Actions Security Analysis with zizmor 30223119716
    result: PASS
    evidence: Exact content head completed successfully.
  - command: python tools/agents/checkpoint.py docs/agents/tasks/FTAI-20260727-liquidation-okx-shadow-acceptance-v1.md --require-checkpoint
    result: PASS
    evidence: Repository validation accepted the compact checkpoint structure and exactly one next_action.
blockers: []
next_action: Verify the ready-state checkpoint commit exact-head CI and unchanged PR 413 mergeability/review state, then guarded squash-merge the declaration and implement inert runner, evaluator and guarded staging workflow infrastructure in a separate PR without a canonical run request.
```
