---
task_id: FTAI-20260731-closure-signal-wizard-context-hardening
status: ready
dispatch_state: READY
branch: agent/closure-signal-wizard-context-hardening
base_branch: develop
created: 2026-07-31
updated: 2026-07-31
parent_task: FTAI-20260730-ai-program-closure-orchestration
related_prs:
  - 825
  - 830
  - 832
owned_paths:
  - docs/agents/tasks/FTAI-20260731-closure-signal-wizard-context-hardening.md
  - ai_platform/portal/signal_wizard/service.py
  - ai_platform/portal/signal_wizard/router.py
  - ai_platform/portal/signal_wizard/models.py
  - ai_platform/portal/signal_wizard/repository.py
  - ai_platform/portal/signal_wizard/migrations/0002_context_hardening.sql
  - tests/ai_platform/portal/signal_wizard/test_signal_wizard.py
  - tests/ai_platform/portal/identity/test_signal_wizard_identity_http.py
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/tasks/FTAI-20260730-ai-program-closure-orchestration.md
  - docs/agents/tasks/FTAI-20260730-closure-ui-signal-wizard.md
  - docs/agents/tasks/FTAI-20260730-closure-signal-wizard-backend.md
  - docs/ai_platform/PROGRAM_CLOSURE_MATRIX.md
  - docs/agents/prompts/ai-program-closure/WORKER-COMMON-RULES.md
---

# Signal Wizard trusted-context and semantic hardening

## Goal

Repair the merged Signal Wizard backend so the identity-enabled same-origin Portal path can construct canonical commands and so every requirement of the original bounded backend task is enforced without mock-only behavior, transient identifiers, fixed-strategy impersonation or authority expansion.

## Proven blockers

1. `IdentityService.resolve_request` generates trusted request and correlation UUIDs only after the upstream request reaches the control plane, while the frozen command body currently must contain those exact UUIDs. A same-origin BFF cannot know them before sending the request.
2. The merged service validates only enabled feature selections and drops disabled selections from the canonical definition.
3. A supplied `base_strategy_version` is reused as the new draft version instead of remaining provenance for a newly derived immutable draft.
4. The preview invents `risk.max_leverage = 1.0` although the command contains no canonical risk input.
5. The persisted preview does not store the exact canonical bound preview command.
6. Submit binds only `resource_id`, not the full persisted target/environment/execution-mode identity.
7. Conflict responses collapse multiple states into one generic reason code and expose raw exception text.
8. Numeric constraints with nonnumeric parameter values do not fail closed.

## Canonical repair

### Trusted command construction

- Keep the frozen `SignalWizardPreviewCommand` and `SignalWizardSubmitCommand` contracts unchanged.
- Authenticate tenant, actor and actor type against `RequestContext`.
- Before digesting, idempotency comparison, persistence or response construction, replace only the command correlation context with `RequestContext.correlation_context()` on the server.
- Treat incoming correlation fields as structurally validated transport input, never as authorization or trusted provenance.
- Preserve target, environment, execution mode, capability, public provenance and all other command fields exactly unless explicit validation rejects them.
- Add an identity-enabled HTTP test through `create_identity_enabled_app`, a real portal session and CSRF enforcement. The body correlation values must intentionally differ from the trusted generated values; the request must succeed only because the application service binds the trusted context before canonicalization.

### Feature and DSL identity

- Resolve and validate every supplied feature selection, including disabled selections.
- Reject any unknown or `approved_for_ai=false` selection regardless of enablement.
- Preserve exact `feature_id`, `enabled`, `timeframe`, resolved parameters and registry definition identity in the canonical preview.
- Require at least one enabled feature.
- Resolve dependencies and validate condition references against the enabled feature set without deleting disabled selections from the canonical request identity.
- Preserve typed DSL validation with no `eval`, `exec`, source generation or compiler authority.

### Durable identity and compatibility

- Always derive a new immutable research-draft strategy version from the canonical trusted command digest.
- Preserve `base_strategy_version` only as provenance; never use it as the new version.
- Remove fabricated risk/runtime compatibility fields. Represent the result explicitly as non-executable research-only draft metadata with all execution, promotion and live-capital authority false.
- Persist the exact canonical trusted preview command JSON together with the result and request digest. Add a forward migration for existing databases.
- Submit must bind to the persisted preview's tenant, actor, resource type, resource ID, environment and execution mode, and must require the exact derived strategy version.
- Keep experiment IDs deterministic and durable; do not create random or transient candidate IDs.

### Errors and fail-closed behavior

- Use stable distinct reason codes for preview idempotency conflict, submit idempotency conflict, target mismatch, environment mismatch, execution-mode mismatch, expected-version mismatch, blocking leakage and corrupt records.
- Return bounded public messages. Never echo raw Pydantic input, credentials, tokens, cookies, headers, private endpoints or arbitrary exception strings.
- Reject numeric minimum/maximum constraints when the resolved value is nonnumeric.
- Add tenant isolation, restart-safe identity, idempotency, compatibility and secret-exclusion coverage.

## Safety boundary

- Research-only; no strategy execution, backtest result fabrication, deployment, approval, promotion, exchange/Vault access, protected-holdout use, order submission or live-capital authority.
- Do not modify frozen contracts, Feature Registry source definitions, Strategy Lab fixed catalog definitions or any frontend Signal Wizard path.
- Do not map selections to `tv_supertrend_v1`, `tv_squeeze_momentum_v1` or any other incompatible fixed strategy.
- Do not add browser-to-Freqtrade, browser-to-exchange or browser-to-Vault paths.

## Validation and merge gate

- Run focused service, persistence and identity-enabled HTTP tests.
- Run every repository workflow required by touched paths.
- Verify the final exact implementation head, all required workflow conclusions and zero unresolved review threads.
- Merge normally into `develop` only after all gates are green.
- After merge, leave exactly one next action: Agent 0 updates the Signal Wizard frontend task and closure matrix to `READY` using the exact merge SHA and exact-head CI evidence.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-31T08:53:00+02:00
head: 28fb301db2c575d610c73143e44bd68c40b46ec7
branch: agent/program-closure-signal-wizard-context-repair-dispatch
pr: null
status: ready
context_routes:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/tasks/FTAI-20260730-ai-program-closure-orchestration.md
  - docs/agents/tasks/FTAI-20260730-closure-ui-signal-wizard.md
  - docs/ai_platform/PROGRAM_CLOSURE_MATRIX.md
owned_paths:
  - docs/agents/tasks/FTAI-20260731-closure-signal-wizard-context-hardening.md
  - ai_platform/portal/signal_wizard/service.py
  - ai_platform/portal/signal_wizard/router.py
  - ai_platform/portal/signal_wizard/models.py
  - ai_platform/portal/signal_wizard/repository.py
  - ai_platform/portal/signal_wizard/migrations/0002_context_hardening.sql
  - tests/ai_platform/portal/signal_wizard/test_signal_wizard.py
  - tests/ai_platform/portal/identity/test_signal_wizard_identity_http.py
proven:
  - Backend PR 825 merged as 0bc35521debd33312820dfad9f010e22aa651610 with green exact-head workflows.
  - Frontend integration blocker PR 832 merged as 28fb301db2c575d610c73143e44bd68c40b46ec7.
  - Open PR path inventory shows no overlap with this task's implementation and test paths.
  - Frozen command contracts expose correlation context but the identity-enabled request context is created only at the upstream boundary.
derived:
  - Server-side trusted correlation binding is the narrowest repair that preserves frozen contracts and backend-authoritative identity.
  - The frontend must remain blocked until both identity-enabled compatibility and semantic hardening are merged.
unknown:
  - Final implementation PR number, exact head, workflow run IDs and merge SHA.
conflicts: []
first_failure:
  marker: SIGNAL_WIZARD_CORRELATION_CONTEXT_UNPROPAGATED
  evidence: The client cannot know trusted UUIDs generated after its request is sent, while the merged service requires exact body equality.
rejected_hypotheses:
  - Guess correlation UUIDs in the BFF.
  - Expose session or identity internals solely to obtain request UUIDs.
  - Trust client correlation values for authorization or provenance.
  - Relax validation only in frontend code or fixtures.
  - Keep generic conflicts, raw exception messages or incomplete target binding.
changed_paths:
  - docs/agents/tasks/FTAI-20260731-closure-signal-wizard-context-hardening.md
validation:
  - command: current develop and open-PR ownership inventory
    result: PASS
    evidence: Assigned paths are bounded and disjoint from open repository PRs.
  - command: merged Signal Wizard service review
    result: BLOCKED
    evidence: The eight proven blockers above remain in develop.
blockers: []
next_action: Start the worker prompt on branch agent/closure-signal-wizard-context-hardening from current develop and open one focused implementation PR.
```
