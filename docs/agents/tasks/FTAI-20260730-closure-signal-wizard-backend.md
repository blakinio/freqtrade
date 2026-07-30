---
task_id: FTAI-20260730-closure-signal-wizard-backend
status: active
branch: agent/closure-signal-wizard-backend
base_branch: develop
created: 2026-07-30
updated: 2026-07-30
related_pr: null
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

## Goal

Implement tenant-scoped durable preview and submit semantics for the frozen Signal Wizard v2 contracts without mapping arbitrary approved features onto incompatible fixed Strategy Lab catalog entries.

## Boundaries

- Preview and submission are research-only and require authenticated model-training permission.
- Only Feature Registry entries with `approved_for_ai=true` may be selected.
- Preview and submit are tenant-bound and idempotent.
- Submitted records are durable research experiment intents; they do not run a strategy, place orders, promote a model or grant live-capital authority.
- No browser, exchange, Vault, protected-holdout, workflow or production-deployment path is added.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-30T22:20:00+02:00
head: 0e3c98086344904c852ecb2b8c5c201353df29ab
branch: agent/closure-signal-wizard-backend
pr: null
status: implementing
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
  - tests/ai_platform/portal/signal_wizard/__init__.py
  - tests/ai_platform/portal/signal_wizard/test_signal_wizard.py
proven:
  - Frozen v2 preview and submit contracts exist on develop.
  - No canonical Signal Wizard service or control-plane routes currently consume them.
  - Active PR 821 and operational PRs 816 and 758 do not overlap the assigned paths.
derived:
  - A dedicated durable backend slice can remove the blocker without redefining shared contracts or Strategy Lab catalog semantics.
unknown:
  - Exact implementation head and CI run identifiers until the PR is opened.
conflicts: []
first_failure:
  marker: MISSING_CANONICAL_SIGNAL_WIZARD_SERVICE
  evidence: UI blocker PR 818 and terminal checkpoint PR 820 found no preview/submit application service.
rejected_hypotheses:
  - Generate transient candidate identifiers in the BFF.
  - Map arbitrary approved features to fixed incompatible Strategy Lab strategies.
  - Grant execution, promotion or live-capital authority.
changed_paths:
  - docs/agents/tasks/FTAI-20260730-closure-signal-wizard-backend.md
validation:
  - command: live ownership and dependency preflight
    result: PASS
    evidence: Frozen contracts and Feature Registry are merged; active changed paths are disjoint.
blockers: []
next_action: Implement the assigned backend, tests and control-plane registration, then open one focused PR.
```
