---
task_id: FTAI-20260730-closure-signal-wizard-backend
status: active
branch: agent/closure-signal-wizard-backend
base_branch: develop
created: 2026-07-30
updated: 2026-07-30
related_pr: 825
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
updated_at: 2026-07-30T22:30:00+02:00
head: 1f0cc85916ef25f6898308f0671c957ef8543cec
branch: agent/closure-signal-wizard-backend
pr: 825
status: validating
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
  - PR 825 implements registered canonical preview and submit routes with durable tenant-scoped storage.
  - Preview validates approved Feature Registry entries, parameters, dependencies and recursive typed condition AST.
  - Submit persists the canonical command and preview-derived research experiment intent without Strategy Lab catalog impersonation.
  - Branch synchronization PR 824 merged current Research Data develop changes normally with no owned-path collision.
derived:
  - A green exact-head merge of PR 825 will satisfy the backend dependency recorded by Signal Wizard UI checkpoint PR 820.
unknown:
  - Exact workflow conclusions and unresolved review-thread count for PR 825.
conflicts: []
first_failure:
  marker: MISSING_CANONICAL_SIGNAL_WIZARD_SERVICE
  evidence: UI blocker PR 818 and terminal checkpoint PR 820 found no preview/submit application service; PR 825 supplies the bounded implementation.
rejected_hypotheses:
  - Generate transient candidate identifiers in the BFF.
  - Map arbitrary approved features to fixed incompatible Strategy Lab strategies.
  - Grant execution, promotion or live-capital authority.
changed_paths:
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
validation:
  - command: live ownership and dependency preflight
    result: PASS
    evidence: Frozen contracts and Feature Registry are merged; active changed paths are disjoint.
  - command: PR 825 exact-head repository CI
    result: PENDING
blockers: []
next_action: Inspect PR 825 exact-head workflows and fix the first failing check inside the assigned paths.
```
