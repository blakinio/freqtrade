---
task_id: FTAI-20260731-signal-wizard-correlation-repair
status: active
project_lane: freqtrade-portal
branch: agent/signal-wizard-correlation-repair-20260731
base_branch: develop
created: 2026-07-31
updated: 2026-07-31
related_task: FTAI-20260730-closure-ui-signal-wizard
owned_paths:
  - docs/agents/tasks/FTAI-20260731-signal-wizard-correlation-repair.md
  - ai_platform/portal/signal_wizard/router.py
  - tests/ai_platform/portal/signal_wizard/test_signal_wizard.py
---

# Signal Wizard trusted correlation repair

## Goal

Remove `SIGNAL_WIZARD_CORRELATION_CONTEXT_UNPROPAGATED` without weakening tenant, actor, actor type, environment, capability, CSRF or research-only validation.

## Design

The identity-enabled control plane generates trusted per-request correlation identifiers after the same-origin BFF has already constructed the command body. The Signal Wizard router therefore replaces only the untrusted command correlation with `RequestContext.correlation_context()` before calling the canonical service. All other command-context fields remain unchanged and continue to fail closed in `SignalWizardService._validate_context`.

## Context checkpoint

```yaml
checkpoint_version: 1
project_lane: freqtrade-portal
phase: implement
session_id: chat-github-20260731-signal-wizard-correlation
execution_mode: chat-github
execution_reason: The sandbox cannot resolve github.com for a checkout; the bounded three-file repair is implemented through the GitHub connector and validated by exact-head CI.
updated_at: 2026-07-31T09:08:00+02:00
lease_expires_at: 2026-07-31T09:53:00+02:00
head: 0b33b354067b36f4c42b2c61d64deb7638c159aa
branch: agent/signal-wizard-correlation-repair-20260731
pr: pending
status: active
proven:
  - PR 832 merged the deterministic identity-enabled correlation blocker into develop as 28fb301db2c575d610c73143e44bd68c40b46ec7.
  - IdentityService creates trusted request_id and correlation_id while authenticating each upstream request.
  - SignalWizardService still validates tenant, actor, actor type, correlation and non-production environment.
  - The router now binds only correlation from the trusted RequestContext before service validation.
  - A new identity-enabled HTTP test generates different trusted identifiers for preview and submit and verifies both responses use them.
derived:
  - The BFF no longer needs to predict upstream request identifiers.
  - Cross-tenant and actor mismatches remain visible to the canonical service and cannot be repaired by the router.
unknown:
  - Exact-head CI conclusions.
conflicts: []
first_failure:
  marker: NONE
  evidence: The previously incompatible correlation requirement now has a bounded backend-authoritative construction path and regression test.
changed_paths:
  - docs/agents/tasks/FTAI-20260731-signal-wizard-correlation-repair.md
  - ai_platform/portal/signal_wizard/router.py
  - tests/ai_platform/portal/signal_wizard/test_signal_wizard.py
validation:
  - command: Local checkout validation
    result: BLOCKED
    evidence: Sandbox DNS cannot resolve github.com; exact-head GitHub Actions are the validation environment.
blockers: []
next_action: Open a focused PR against develop and require exact-head AI Platform, Freqtrade and security checks before normal merge.
```
