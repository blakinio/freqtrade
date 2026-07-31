---
task_id: FTAI-20260731-closure-signal-wizard-context-hardening
status: ready
dispatch_state: READY
branch: agent/closure-signal-wizard-semantic-hardening
base_branch: develop
created: 2026-07-31
updated: 2026-07-31
parent_task: FTAI-20260730-ai-program-closure-orchestration
correlation_task: FTAI-20260731-signal-wizard-context-repair
correlation_pr: 846
correlation_merge: 367a51b610d2a34ee5841bc0b86622bd64fc6858
superseded_pr: 844
related_prs:
  - 825
  - 830
  - 832
  - 846
owned_paths:
  - docs/agents/tasks/FTAI-20260731-closure-signal-wizard-context-hardening.md
  - ai_platform/portal/signal_wizard/service.py
  - ai_platform/portal/signal_wizard/router.py
  - ai_platform/portal/signal_wizard/models.py
  - ai_platform/portal/signal_wizard/repository.py
  - ai_platform/portal/signal_wizard/migrations/0002_semantic_hardening.sql
  - tests/ai_platform/portal/signal_wizard/test_signal_wizard_semantic_hardening.py
  - tests/ai_platform/portal/signal_wizard/test_signal_wizard_identity_http.py
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/tasks/FTAI-20260730-ai-program-closure-orchestration.md
  - docs/agents/tasks/FTAI-20260730-closure-ui-signal-wizard.md
  - docs/agents/tasks/FTAI-20260730-closure-signal-wizard-backend.md
  - docs/agents/tasks/FTAI-20260731-signal-wizard-context-repair.md
  - docs/ai_platform/PROGRAM_CLOSURE_MATRIX.md
  - docs/agents/prompts/ai-program-closure/WORKER-COMMON-RULES.md
---

# Signal Wizard semantic and persistence hardening

## Goal

Repair the remaining semantic, durable-persistence and public-error gaps in the merged Signal Wizard backend while preserving the authenticated context construction merged through PR #846.

## Verified dependency and ownership transfer

- PR #846 merged normally as `367a51b610d2a34ee5841bc0b86622bd64fc6858`.
- Exact implementation head `647ea9fb79134e90af87f165ea1529482f2c1f5c` passed AI Platform CI `30612077198`, Freqtrade CI `30612077288` and security `30612077128`.
- PR #846 had zero review threads.
- Competing PR #844 was closed as superseded and must not be revived.
- Live open-PR search after closing #844 showed no Signal Wizard implementation PR and no overlap with the owned implementation/test paths below.
- Agent 0 created `agent/closure-signal-wizard-semantic-hardening` from current `develop` after that verification.

## Proven semantic blockers

1. The merged service validates only enabled feature selections and drops disabled selections from canonical identity.
2. A supplied `base_strategy_version` is reused as the new draft version instead of remaining provenance for a newly derived immutable research draft.
3. Preview invents `risk.max_leverage = 1.0` although no canonical risk input exists.
4. The persisted preview does not store the exact canonical trusted preview command.
5. Submit binds only `resource_id`, not the full persisted actor/target/environment/execution-mode identity.
6. Numeric minimum/maximum constraints with nonnumeric values do not fail closed.
7. Conflict responses collapse distinct states into generic codes and may expose raw exception text.

## Required repair

### Authenticated context compatibility

- Preserve PR #846 server-side construction of stable trusted command correlation from authenticated tenant, actor, operation and normalized idempotency key.
- Never trust browser-supplied correlation or weaken tenant, actor, actor type, capability, CSRF or non-production enforcement.
- Keep retry identity deterministic and durable without introducing random/transient candidate identifiers.

### Feature and DSL identity

- Resolve and validate every supplied feature selection, including disabled selections.
- Reject any unknown or `approved_for_ai=false` selection regardless of enablement.
- Preserve exact `feature_id`, `enabled`, `timeframe`, resolved parameters and registry definition identity in the canonical preview.
- Require at least one enabled feature.
- Resolve dependencies and validate condition references against the enabled feature set without deleting disabled selections from canonical request identity.
- Preserve typed DSL validation with no `eval`, `exec`, source generation or compiler authority.

### Durable draft identity

- Always derive a new immutable research-draft strategy version from the canonical trusted command digest.
- Preserve `base_strategy_version` only as provenance; never use it as the new draft version.
- Remove fabricated risk/runtime compatibility fields. Represent the result explicitly as non-executable research-only draft metadata with execution, promotion and live-capital authority false.
- Persist the exact canonical trusted preview command JSON together with result JSON, request digest and derived version.
- Add a forward migration for existing databases; do not rewrite or mutate migration `0001_signal_wizard.sql`.
- Add restart-safe tests proving exact persisted command/result identity survives a new service/session instance.

### Submit binding and fail-closed validation

- Submit must bind to the persisted preview's tenant, actor, actor type, resource type, resource ID, environment and execution mode.
- Require the exact derived strategy version.
- Preserve deterministic durable experiment ID and tenant-scoped idempotency.
- Add stable distinct service/router reason codes for preview idempotency, submit idempotency, target mismatch, environment mismatch, execution-mode mismatch, actor mismatch, version mismatch, blocking leakage and corrupt records.
- Return bounded public messages. Never echo raw Pydantic input, cookies, tokens, headers, credentials, private endpoints or arbitrary exception text.
- Reject numeric minimum/maximum constraints when the resolved parameter value is nonnumeric.
- Add service, persistence, tenant isolation, identity-enabled error-shape, restart-safe idempotency, compatibility and secret-exclusion coverage.

## Safety boundary

- Research-only; no strategy execution, backtest result fabrication, deployment, approval, promotion, exchange/Vault access, protected-holdout use, order submission or live-capital authority.
- Do not modify frozen contracts, Feature Registry source definitions, Strategy Lab fixed catalog definitions or any frontend Signal Wizard path.
- Do not map selections to `tv_supertrend_v1`, `tv_squeeze_momentum_v1` or any incompatible fixed strategy.
- Do not create random or transient candidate IDs.

## Validation and merge gate

- Before editing, repeat current `develop`, active-task and open-PR overlap checks.
- Continue only on `agent/closure-signal-wizard-semantic-hardening` and do not create a duplicate task or branch.
- Run focused service/persistence/identity-enabled tests and all repository workflows required by touched paths.
- Verify final exact implementation head, all required workflow conclusions and zero unresolved review threads.
- Merge normally into `develop` only after all gates are green.
- After merge, leave exactly one next action: Agent 0 updates the Signal Wizard frontend task and closure matrix to `READY` using exact merge SHA and exact-head CI evidence.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-31T09:45:00+02:00
head: 367a51b610d2a34ee5841bc0b86622bd64fc6858
branch: agent/closure-signal-wizard-semantic-hardening
pr: null
status: ready
context_routes:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/tasks/FTAI-20260730-ai-program-closure-orchestration.md
  - docs/agents/tasks/FTAI-20260730-closure-ui-signal-wizard.md
  - docs/agents/tasks/FTAI-20260731-signal-wizard-context-repair.md
  - docs/ai_platform/PROGRAM_CLOSURE_MATRIX.md
owned_paths:
  - docs/agents/tasks/FTAI-20260731-closure-signal-wizard-context-hardening.md
  - ai_platform/portal/signal_wizard/service.py
  - ai_platform/portal/signal_wizard/router.py
  - ai_platform/portal/signal_wizard/models.py
  - ai_platform/portal/signal_wizard/repository.py
  - ai_platform/portal/signal_wizard/migrations/0002_semantic_hardening.sql
  - tests/ai_platform/portal/signal_wizard/test_signal_wizard_semantic_hardening.py
  - tests/ai_platform/portal/signal_wizard/test_signal_wizard_identity_http.py
proven:
  - Backend PR 825 merged as 0bc35521debd33312820dfad9f010e22aa651610 with green exact-head workflows.
  - Frontend blocker PR 832 merged as 28fb301db2c575d610c73143e44bd68c40b46ec7.
  - Authenticated context PR 846 merged as 367a51b610d2a34ee5841bc0b86622bd64fc6858 from exact head 647ea9fb79134e90af87f165ea1529482f2c1f5c.
  - PR 846 exact-head AI Platform, Freqtrade and security workflows succeeded and its review-thread count was zero.
  - PR 844 was closed as a superseded competing implementation.
  - Live open-PR search showed only governance PR 851 for Signal Wizard; no active implementation path overlaps this task.
  - Final backend code still contains the seven semantic blockers listed above.
derived:
  - Correlation compatibility is complete; remaining work is one bounded backend/API semantic and persistence task.
  - The frontend must remain WAIT_FOR_BACKEND until this task merges with exact-head evidence.
unknown:
  - Semantic-hardening implementation PR number, exact head, workflow run IDs and merge SHA.
conflicts: []
first_failure:
  marker: SIGNAL_WIZARD_SEMANTIC_IDENTITY_INCOMPLETE
  evidence: The merged service drops disabled feature identity, can reuse a base version as a new draft, fabricates risk compatibility and persists incomplete preview identity.
rejected_hypotheses:
  - Revive or merge superseded PR 844.
  - Modify frozen contracts or frontend paths.
  - Keep generic/raw error responses, incomplete target binding or nonnumeric constraint fall-through.
  - Generate transient IDs or map to fixed Strategy Lab strategies.
changed_paths:
  - docs/agents/tasks/FTAI-20260731-closure-signal-wizard-context-hardening.md
validation:
  - command: PR 846 exact-head workflow and review audit
    result: PASS
    evidence: Runs 30612077198, 30612077288 and 30612077128 succeeded; zero review threads.
  - command: live open-PR Signal Wizard inventory
    result: PASS
    evidence: PR 844 is closed and no implementation PR owns the assigned paths.
  - command: merged Signal Wizard semantic review
    result: BLOCKED
    evidence: The seven bounded semantic/persistence/error blockers remain on develop.
blockers: []
next_action: Run docs/agents/prompts/ai-program-closure/SIGNAL-WIZARD-CONTEXT-HARDENING-AGENT-PROMPT.md on agent/closure-signal-wizard-semantic-hardening and open one focused implementation PR.
```
