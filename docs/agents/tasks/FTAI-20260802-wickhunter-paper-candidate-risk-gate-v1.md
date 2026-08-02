---
task_id: FTAI-20260802-wickhunter-paper-candidate-risk-gate-v1
project_lane: freqtrade-wickhunter
status: validating
branch: fix/wickhunter-paper-candidate-risk-gate-v1
base_branch: develop
created: 2026-08-02
updated: 2026-08-02
related_pr: 1032
depends_on:
  - FTAI-20260801-wickhunter-wh09-paper-validation-v1
owned_paths:
  - ai_platform/wickhunter/risk.py
  - tests/ai_platform_integration/test_wickhunter_candidate_paper_risk_gate.py
  - docs/ai_platform/WICKHUNTER_CANDIDATE_PAPER_RISK_GATE.md
  - docs/agents/tasks/FTAI-20260802-wickhunter-paper-candidate-risk-gate-v1.md
---

# WickHunter candidate paper risk gate

## Objective

Allow an immutable supervised model in candidate state to pass the deterministic risk engine only for explicitly authorized read-only SHADOW/PAPER validation, while keeping every production and default path fail-closed.

## Acceptance

- authorization flag defaults to false;
- candidate model remains rejected without the flag;
- flag is effective only in SHADOW or PAPER;
- RESEARCH and LIVE remain unauthorized;
- all other risk checks remain unchanged;
- no promotion, credentials, order adapter, orders, execution or live capital.

## Checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-08-02T14:40:00+02:00
phase: validation
status: validating
branch: fix/wickhunter-paper-candidate-risk-gate-v1
base_branch: develop
proven:
  - WH-09 requires at least one simulated allowed decision
  - the existing supervised-model gate otherwise rejects every candidate model
  - the new authorization is explicit, default-off and mode-restricted
next_action: run focused and exact-head repository validation, repair findings, audit the four declared paths and merge only on unchanged green SHA
```
