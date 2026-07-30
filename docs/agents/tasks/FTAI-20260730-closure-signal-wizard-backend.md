---
task_id: FTAI-20260730-closure-signal-wizard-backend
status: completed
branch: agent/closure-signal-wizard-unblock
base_branch: develop
created: 2026-07-30
updated: 2026-07-30
related_pr: 825
terminal_pr: 830
dependencies:
  - FTAI-20260730-closure-contracts merged as 6e489f7e10199120424cbcd01b3e125711630243
  - Signal Wizard blocker checkpoint merged as 18881d8847c765e939509a0f34b9dc327c5c9270
owned_paths:
  - docs/agents/tasks/FTAI-20260730-closure-signal-wizard-backend.md
  - ai_platform/portal/signal_wizard/__init__.py
  - ai_platform/portal/signal_wizard/models.py
  - ai_platform/portal/signal_wizard/repository.py
  - ai_platform/portal/signal_wizard/router.py
  - ai_platform/portal/signal_wizard/service.py
  - ai_platform/portal/signal_wizard/migrations/0001_signal_wizard.sql
  - ai_platform/portal/control_plane/api.py
  - ai_platform/portal/control_plane/database.py
  - tests/ai_platform/portal/control_plane/test_api.py
  - tests/ai_platform/portal/operations/test_private_runtime_reconciliation.py
  - tests/ai_platform/portal/signal_wizard/__init__.py
  - tests/ai_platform/portal/signal_wizard/test_signal_wizard.py
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/prompts/ai-program-closure/WORKER-COMMON-RULES.md
  - docs/agents/tasks/FTAI-20260730-closure-ui-signal-wizard.md
  - docs/ai_platform/PROGRAM_CLOSURE_MATRIX.md
---

# Canonical Signal Wizard backend

## Terminal result

- Implementation PR #825 merged normally into `develop` as `0bc35521debd33312820dfad9f010e22aa651610`.
- The control plane now exposes tenant-scoped `/v1/signal-wizard/preview` and `/v1/signal-wizard/submit` endpoints.
- Preview consumes the frozen v2 contracts, validates authenticated context, `approved_for_ai` registry entries, parameters, explicit dependencies and recursive typed DSL conditions.
- Preview definitions and hashes are deterministic and preserve registry snapshot identity, closed-bar semantics, provenance and zero execution authority.
- Submit requires the persisted preview and expected strategy version, then stores the canonical command and durable research experiment intent with tenant-scoped idempotency.
- No fixed Strategy Lab catalog identity is impersonated and no strategy run, order, deployment, promotion, protected-holdout or live-capital authority is introduced.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-30T23:36:00+02:00
head: 0bc35521debd33312820dfad9f010e22aa651610
branch: agent/closure-signal-wizard-unblock
pr: 830
status: ready
context_routes:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/tasks/FTAI-20260730-closure-ui-signal-wizard.md
  - docs/ai_platform/PROGRAM_CLOSURE_MATRIX.md
owned_paths:
  - docs/agents/tasks/FTAI-20260730-closure-signal-wizard-backend.md
  - ai_platform/portal/signal_wizard/__init__.py
  - ai_platform/portal/signal_wizard/models.py
  - ai_platform/portal/signal_wizard/repository.py
  - ai_platform/portal/signal_wizard/router.py
  - ai_platform/portal/signal_wizard/service.py
  - ai_platform/portal/signal_wizard/migrations/0001_signal_wizard.sql
  - ai_platform/portal/control_plane/api.py
  - ai_platform/portal/control_plane/database.py
  - tests/ai_platform/portal/control_plane/test_api.py
  - tests/ai_platform/portal/operations/test_private_runtime_reconciliation.py
  - tests/ai_platform/portal/signal_wizard/__init__.py
  - tests/ai_platform/portal/signal_wizard/test_signal_wizard.py
proven:
  - PR 825 exact head 47c042846094f43a8dc06494b177d3d69c64878d passed AI Platform CI run 30582265385.
  - The same exact head passed AI Strategy Engine run 30582265713 and GitHub Actions Security Analysis run 30582265752.
  - Freqtrade CI run 30582265405 passed pre-commit, documentation, Python 3.11 through 3.14, 5870-test coverage, distribution build and terminal CI Gate.
  - PR 825 changed exactly thirteen assigned paths and had zero unresolved review threads.
  - PR 825 merged normally as 0bc35521debd33312820dfad9f010e22aa651610.
  - Registered OpenAPI contains both canonical Signal Wizard routes without private transport or credential material.
derived:
  - The backend dependency recorded by UI blocker PRs 818 and 820 is satisfied.
  - The Signal Wizard frontend task can return to READY without backend ownership transfer or mock-only behavior.
unknown: []
conflicts: []
first_failure:
  marker: PRIVATE_RUNTIME_OPENAPI_ASSERTION_TOO_BROAD
  evidence: An inherited regression rejected the public frozen field authorization_decision_ref by substring; the repair narrowed the test to actual private endpoint and authorization-header material, after which all exact-head gates passed.
rejected_hypotheses:
  - Generate transient candidate identifiers in the BFF.
  - Map arbitrary approved features to fixed incompatible Strategy Lab strategies.
  - Hide canonical routes or falsify their typed OpenAPI contract.
  - Grant execution, promotion or live-capital authority.
changed_paths:
  - docs/agents/tasks/FTAI-20260730-closure-signal-wizard-backend.md
validation:
  - command: AI Platform CI run 30582265385
    result: PASS
    evidence: Exact final head passed the complete AI Platform package and API contract suite.
  - command: AI Strategy Engine run 30582265713
    result: PASS
    evidence: Exact final head passed package, type, deterministic and boundary checks.
  - command: Freqtrade CI run 30582265405
    result: PASS
    evidence: Exact final head passed all required matrix jobs and terminal CI Gate.
  - command: GitHub Actions Security Analysis run 30582265752
    result: PASS
    evidence: Exact final head passed zizmor analysis.
  - command: PR 825 changed-file, review and merge audit
    result: PASS
    evidence: Thirteen assigned paths, zero unresolved threads and normal squash merge 0bc35521debd33312820dfad9f010e22aa651610.
blockers: []
next_action: Signal Wizard frontend is READY; the owner may manually start its canonical UI prompt from current develop.
```
