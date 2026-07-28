---
task_id: FTAI-20260728-liquidation-okx-shadow-acceptance-python3-bootstrap-v1
status: validating
branch: ops/okx-shadow-acceptance-24h-20260728-v3
base_branch: develop
created: 2026-07-28
updated: 2026-07-28
required_reads:
  - .github/workflows/ai-platform-okx-liquidation-shadow-acceptance.yml
  - docs/ai_platform/LIQUIDATION_OKX_SHADOW_ACCEPTANCE_EXECUTION.md
search_first:
  - PR #624 and workflow run 30358400049 job 90271896559
optional_reads:
  - ai_platform/research/liquidations/okx-liquidation-shadow-acceptance-policy-v1.json
owned_paths:
  - docs/agents/tasks/FTAI-20260728-liquidation-okx-shadow-acceptance-python3-bootstrap-v1.md
  - .github/workflows/ai-platform-okx-liquidation-shadow-acceptance.yml
  - tests/ai_platform_integration/test_liquidation_okx_shadow_acceptance_workflow_mapping.py
---

# OKX 24-hour shadow acceptance

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-28T19:51:51+02:00
head: 2a6accbf6b6c21233d897c4ab419debd0aec72a6
branch: ops/okx-shadow-acceptance-24h-20260728-v3
pr: "#624"
status: validating
context_routes:
  - .github/workflows/ai-platform-okx-liquidation-shadow-acceptance.yml
  - docs/ai_platform/LIQUIDATION_OKX_SHADOW_ACCEPTANCE_EXECUTION.md
  - ai_platform/research/liquidations/okx-liquidation-shadow-acceptance-policy-v1.json
  - ai_platform/research/liquidations/run-requests/okx-shadow-acceptance-20260727-v1.json
owned_paths:
  - docs/agents/tasks/FTAI-20260728-liquidation-okx-shadow-acceptance-python3-bootstrap-v1.md
  - .github/workflows/ai-platform-okx-liquidation-shadow-acceptance.yml
  - tests/ai_platform_integration/test_liquidation_okx_shadow_acceptance_workflow_mapping.py
proven:
  - Python bootstrap repair PR 617 merged as d86e2a33a1ac155f794782da23bb27b2e401b2fe.
  - Trigger PR 624 is open and unmerged with exactly one frozen request file at head 2a6accbf6b6c21233d897c4ab419debd0aec72a6.
  - Exact-head AI Platform CI 30358400117, Freqtrade CI 30358400244 and zizmor 30358400238 completed successfully.
  - Workflow run 30358400049 job 90271896559 is running on freqtrade-synology-staging.
  - Exact-one-file scope, durable-storage preparation, credential refusal, Python setup and public collector dependency installation passed.
  - The frozen acceptance package is currently collecting; evaluator, terminal report and bounded artifact steps have not run.
  - Request safety remains credential-free with execution, replay, model training and performance research disabled and orders submitted zero.
derived:
  - The active run crossed every pre-collection gate and is collecting public OKX shadow data.
  - Trigger PR 624 must remain open and must never be merged until terminal evidence is captured.
unknown:
  - Terminal outcome: accepted, rejected or inconclusive_insufficient_activity.
  - Final report, manifest, checksum identities, event activity and health-gate results.
conflicts: []
first_failure:
  marker: OKX_ACCEPTANCE_BOOTSTRAP_PYTHON_COMMAND_MISSING
  evidence: Prior trigger PR 611 failed before collection because validation invoked python before setup; PR 617 changed only that bootstrap command to python3 and the active run passed the repaired gate.
rejected_hypotheses:
  - The active run is blocked by runner routing, durable storage, trading credentials or Python bootstrap.
  - The exact-one-file trigger may be merged.
changed_paths:
  - ai_platform/research/liquidations/run-requests/okx-shadow-acceptance-20260727-v1.json
validation:
  - command: PR 624 exact-one-file diff
    result: PASS
    evidence: PR metadata reports one commit, one changed file and twenty added lines at the frozen request path.
  - command: Exact-head repository CI
    result: PASS
    evidence: AI Platform CI 30358400117, Freqtrade CI 30358400244 and zizmor 30358400238 succeeded at 2a6accbf6b6c21233d897c4ab419debd0aec72a6.
  - command: OKX acceptance pre-collection gates
    result: PASS
    evidence: Job 90271896559 completed steps 1 through 7 successfully and entered Run frozen acceptance package.
  - command: Terminal evaluator and bounded artifact verification
    result: NOT_RUN
    evidence: Workflow run 30358400049 remains in progress in the 24-hour collector step.
blockers: []
next_action: Monitor workflow run 30358400049 job 90271896559 to a terminal state, then fetch logs and the bounded artifact, verify the report, manifest, checksum index and safety fields, close PR 624 without merge, and record the accepted, rejected or inconclusive_insufficient_activity outcome.
```
