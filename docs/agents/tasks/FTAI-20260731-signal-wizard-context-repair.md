---
task_id: FTAI-20260731-signal-wizard-context-repair
status: in_progress
dispatch_state: ACTIVE
branch: agent/closure-signal-wizard-context-repair
base_branch: develop
created: 2026-07-31
updated: 2026-07-31
parent_task: FTAI-20260730-closure-ui-signal-wizard
blocker_pr: 832
owned_paths:
  - docs/agents/tasks/FTAI-20260731-signal-wizard-context-repair.md
  - ai_platform/portal/signal_wizard/router.py
  - tests/ai_platform/portal/signal_wizard/test_signal_wizard_identity_http.py
---

# Signal Wizard authenticated context repair

## Goal

Remove `SIGNAL_WIZARD_CORRELATION_CONTEXT_UNPROPAGATED` without weakening authenticated tenant, actor, capability, CSRF, research-only or no-live-authority enforcement.

## Bounded decision

The authenticated Signal Wizard router constructs command correlation after identity authentication. It derives stable request and correlation UUIDs from trusted tenant, trusted actor, operation and normalized idempotency key. Browser-provided correlation is replaced and never treated as authority.

This preserves durable idempotency across retries even though `IdentityService` intentionally creates fresh HTTP request identifiers for every authenticated request. Tenant, actor and actor type remain command fields checked against the trusted authenticated context by `SignalWizardService`.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-31T09:05:00+02:00
head: 3b87fdb77cfc8cb088cc60f16f09302b4c6b08c9
branch: agent/closure-signal-wizard-context-repair
pr: null
status: in_progress
context_routes:
  - AGENTS.md
  - docs/agents/prompts/ai-program-closure/WORKER-COMMON-RULES.md
  - docs/agents/tasks/FTAI-20260730-closure-ui-signal-wizard.md
owned_paths:
  - docs/agents/tasks/FTAI-20260731-signal-wizard-context-repair.md
  - ai_platform/portal/signal_wizard/router.py
  - tests/ai_platform/portal/signal_wizard/test_signal_wizard_identity_http.py
proven:
  - PR 832 merged as 28fb301db2c575d610c73143e44bd68c40b46ec7 and records the identity-enabled correlation blocker.
  - IdentityService generates fresh HTTP request_id and correlation_id after the BFF has constructed its body.
  - SignalWizardService verifies authenticated tenant, actor, actor type and command correlation equality.
  - Stable correlation derived inside the authenticated router can satisfy service validation without trusting browser correlation.
derived:
  - The repair can remain router-local and does not require changing frozen contracts or IdentityService.
  - Reusing the normalized idempotency key makes correlation stable across retries while different command bodies still reach existing idempotency conflict checks.
unknown:
  - Exact-head repository CI and review state.
conflicts: []
first_failure:
  marker: NONE
  evidence: Bounded implementation and identity-enabled regression coverage are committed.
rejected_hypotheses:
  - Expose fresh IdentityService request UUIDs to the browser before authentication.
  - Trust or guess correlation UUIDs supplied by the browser.
  - Remove tenant, actor or correlation validation from SignalWizardService.
  - Make IdentityService request identifiers deterministic globally.
changed_paths:
  - ai_platform/portal/signal_wizard/router.py
  - tests/ai_platform/portal/signal_wizard/test_signal_wizard_identity_http.py
  - docs/agents/tasks/FTAI-20260731-signal-wizard-context-repair.md
validation:
  - command: Identity-enabled Signal Wizard HTTP regression
    result: PENDING_CI
    evidence: Test covers login, CSRF, preview retry, submit retry, server-bound correlation and actor mismatch.
blockers: []
next_action: Open the focused repair PR, fix only evidenced CI or review failures, and merge normally after exact-head gates pass.
```
