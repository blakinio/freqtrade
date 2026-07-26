---
task_id: FTAI-20260727-liquidation-okx-shadow-acceptance-v1
status: validating
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
updated_at: 2026-07-27T00:25:00+02:00
head: 50a6ecc80cfd998551c85f45cbed3e41c51ef38f
branch: docs/okx-shadow-acceptance-policy-v1
pr: "#413"
status: validating
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
derived:
  - The first long run should preserve the two-symbol smoke contract; broad-universe or liquid20-v2 membership is a later package.
  - A GitHub-hosted runner is not eligible for continuous 24-hour capture and durable raw evidence.
  - Zero or sparse events must not produce acceptance; healthy low-activity runs should be inconclusive rather than falsely rejected for transport quality.
unknown:
  - Exact implementation design for the inert runner, evaluator and guarded staging workflow.
  - Whether the intended non-restricted always-on Linux staging host will pass the frozen gates.
  - Final exact-head repository CI, mergeability and review result for PR 413.
conflicts: []
first_failure:
  marker: none
  evidence: No implementation or operational run is included; declaration validation has not reached terminal CI.
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
  - command: repository exact-head CI
    result: NOT_RUN
    evidence: PR 413 has opened and its final metadata head has not reached terminal CI.
  - command: python tools/agents/checkpoint.py docs/agents/tasks/FTAI-20260727-liquidation-okx-shadow-acceptance-v1.md --require-checkpoint
    result: NOT_RUN
    evidence: No local checkout is available; repository CI is authoritative for PR 413.
blockers: []
next_action: Verify PR 413 exact-head AI Platform CI, Freqtrade CI, zizmor, mergeability and review state; fix only confirmed failures, merge the declaration if green, then implement inert runner, evaluator and guarded staging workflow infrastructure in a separate PR without a canonical run request.
```
